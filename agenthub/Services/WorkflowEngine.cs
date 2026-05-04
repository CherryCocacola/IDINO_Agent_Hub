using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Models;
using Microsoft.EntityFrameworkCore;
using System.Text.Json;
using System.Collections.Generic;
using System.Text;

namespace AIAgentManagement.Services;

public class WorkflowEngine : IWorkflowEngine
{
    private readonly AIAgentManagementDbContext _context;
    private readonly IAgentService _agentService;
    private readonly IChatService _chatService;
    private readonly IToolExecutionService _toolExecutionService;
    private readonly IAiProxyService _aiProxyService;
    private readonly ILogger<WorkflowEngine> _logger;

    public WorkflowEngine(
        AIAgentManagementDbContext context,
        IAgentService agentService,
        IChatService chatService,
        IToolExecutionService toolExecutionService,
        IAiProxyService aiProxyService,
        ILogger<WorkflowEngine> logger)
    {
        _context = context;
        _agentService = agentService;
        _chatService = chatService;
        _toolExecutionService = toolExecutionService;
        _aiProxyService = aiProxyService;
        _logger = logger;
    }

    public async Task<WorkflowExecutionResult> ExecuteAsync(int workflowId, string? inputData, CancellationToken cancellationToken = default)
    {
        var startTime = DateTime.UtcNow;
        var result = new WorkflowExecutionResult();

        try
        {
            // Workflow 로드
            var workflow = await _context.Workflows
                .Include(w => w.WorkflowNodes)
                .FirstOrDefaultAsync(w => w.WorkflowId == workflowId && w.IsActive, cancellationToken);

            if (workflow == null)
            {
                result.Success = false;
                result.ErrorMessage = $"Workflow {workflowId} not found or inactive";
                return result;
            }

            var nodes = workflow.WorkflowNodes.OrderBy(n => n.SortOrder).ToList();

            if (!nodes.Any())
            {
                result.Success = false;
                result.ErrorMessage = "Workflow has no nodes";
                return result;
            }

            // DAG 분석 및 실행 순서 결정
            var executionOrder = DetermineExecutionOrder(nodes);
            var nodeData = new Dictionary<int, string?> { { 0, inputData } }; // 초기 입력

            // 각 노드 순차 실행
            foreach (var nodeGroup in executionOrder)
            {
                // 병렬 실행 가능한 노드들
                var parallelTasks = nodeGroup.Select(async node =>
                {
                    var nodeInput = GetNodeInput(node, nodeData, nodes);
                    var nodeResult = await ExecuteNodeAsync(node, nodeInput, cancellationToken);
                    nodeData[node.NodeId] = nodeResult.OutputData;
                    return new { NodeId = node.NodeId, Result = nodeResult };
                });

                var nodeResults = await Task.WhenAll(parallelTasks);

                foreach (var nodeResult in nodeResults)
                {
                    result.NodeResults[nodeResult.NodeId] = nodeResult.Result;

                    if (nodeResult.Result.Status == "Failed")
                    {
                        result.Success = false;
                        result.ErrorMessage = $"Node {nodeResult.NodeId} failed: {nodeResult.Result.ErrorMessage}";
                        result.TotalExecutionTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
                        return result;
                    }
                }
            }

            // 최종 출력은 마지막 노드의 출력
            var lastNode = nodes.OrderByDescending(n => n.SortOrder).First();
            result.OutputData = nodeData.TryGetValue(lastNode.NodeId, out var output) ? output : inputData;
            result.Success = true;
            result.TotalExecutionTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing workflow {WorkflowId}", workflowId);
            result.Success = false;
            result.ErrorMessage = ex.Message;
            result.TotalExecutionTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        }

        return result;
    }

    private List<List<WorkflowNode>> DetermineExecutionOrder(List<WorkflowNode> nodes)
    {
        // 간단한 위상 정렬 구현
        var inDegree = new Dictionary<int, int>();
        var graph = new Dictionary<int, List<int>>();

        // 초기화
        foreach (var node in nodes)
        {
            inDegree[node.NodeId] = 0;
            graph[node.NodeId] = new List<int>();
        }

        // 연결 정보 파싱 및 그래프 구성
        foreach (var node in nodes)
        {
            if (!string.IsNullOrEmpty(node.Connections))
            {
                try
                {
                    var connections = JsonSerializer.Deserialize<Dictionary<string, List<int>>>(node.Connections);
                    if (connections != null && connections.ContainsKey("targets"))
                    {
                        foreach (var targetId in connections["targets"])
                        {
                            if (graph.ContainsKey(targetId))
                            {
                                graph[node.NodeId].Add(targetId);
                                inDegree[targetId]++;
                            }
                        }
                    }
                }
                catch
                {
                    // 연결 정보 파싱 실패 시 무시
                }
            }
        }

        // 위상 정렬
        var result = new List<List<WorkflowNode>>();
        var queue = new Queue<WorkflowNode>();

        // 진입 차수가 0인 노드들 찾기
        foreach (var node in nodes)
        {
            if (inDegree[node.NodeId] == 0)
            {
                queue.Enqueue(node);
            }
        }

        while (queue.Count > 0)
        {
            var currentLevel = new List<WorkflowNode>();
            var levelSize = queue.Count;

            for (int i = 0; i < levelSize; i++)
            {
                var node = queue.Dequeue();
                currentLevel.Add(node);

                foreach (var targetId in graph[node.NodeId])
                {
                    inDegree[targetId]--;
                    if (inDegree[targetId] == 0)
                    {
                        var targetNode = nodes.FirstOrDefault(n => n.NodeId == targetId);
                        if (targetNode != null)
                        {
                            queue.Enqueue(targetNode);
                        }
                    }
                }
            }

            if (currentLevel.Any())
            {
                result.Add(currentLevel);
            }
        }

        return result;
    }

    private string? GetNodeInput(WorkflowNode node, Dictionary<int, string?> nodeData, List<WorkflowNode> allNodes)
    {
        if (string.IsNullOrEmpty(node.Connections))
        {
            // 연결이 없으면 초기 입력 사용
            return nodeData.TryGetValue(0, out var initialInput) ? initialInput : null;
        }

        try
        {
            var connections = JsonSerializer.Deserialize<Dictionary<string, List<int>>>(node.Connections);
            if (connections != null && connections.ContainsKey("sources"))
            {
                var sources = connections["sources"];
                if (sources.Any())
                {
                    // 첫 번째 소스의 출력 사용 (간단한 구현)
                    var sourceId = sources.First();
                    return nodeData.TryGetValue(sourceId, out var sourceOutput) ? sourceOutput : null;
                }
            }
        }
        catch
        {
            // 파싱 실패 시 초기 입력 사용
        }

        return nodeData.TryGetValue(0, out var input) ? input : null;
    }

    private async Task<NodeExecutionResult> ExecuteNodeAsync(WorkflowNode node, string? inputData, CancellationToken cancellationToken)
    {
        var startTime = DateTime.UtcNow;
        var result = new NodeExecutionResult
        {
            NodeId = node.NodeId,
            InputData = inputData
        };

        try
        {
            switch (node.NodeType.ToLower())
            {
                case "agent":
                    result.OutputData = await ExecuteAgentNodeAsync(node, inputData, cancellationToken);
                    break;

                case "llm":
                    result.OutputData = await ExecuteLlmNodeAsync(node, inputData, cancellationToken);
                    break;

                case "tool":
                    result.OutputData = await ExecuteToolNodeAsync(node, inputData, cancellationToken);
                    break;

                case "condition":
                    result.OutputData = await ExecuteConditionNodeAsync(node, inputData, cancellationToken);
                    break;

                case "datatransform":
                    result.OutputData = await ExecuteDataTransformNodeAsync(node, inputData, cancellationToken);
                    break;

                default:
                    result.OutputData = inputData; // 기본적으로 입력을 그대로 전달
                    break;
            }

            result.Status = "Completed";
            result.ExecutionTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        }
        catch (Exception ex)
        {
            result.Status = "Failed";
            result.ErrorMessage = ex.Message;
            result.ExecutionTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
            _logger.LogError(ex, "Error executing node {NodeId}", node.NodeId);
        }

        return result;
    }

    private async Task<string?> ExecuteAgentNodeAsync(WorkflowNode node, string? inputData, CancellationToken cancellationToken)
    {
        var config = JsonSerializer.Deserialize<Dictionary<string, object>>(node.NodeConfig ?? "{}");
        if (config == null || !config.ContainsKey("agentId"))
        {
            throw new InvalidOperationException("Agent node must have agentId in config");
        }

        var agentId = Convert.ToInt32(config["agentId"]);
        var agent = await _agentService.GetAgentByIdAsync(agentId);
        if (agent == null)
        {
            throw new InvalidOperationException($"Agent {agentId} not found");
        }

        // Agent 실행 로직 (간단한 구현)
        var message = inputData ?? "";
        // 실제로는 ChatService를 통해 Agent와 대화를 시작해야 함
        return JsonSerializer.Serialize(new { result = $"Agent {agent.AgentName} processed: {message}" });
    }

    private async Task<string?> ExecuteLlmNodeAsync(WorkflowNode node, string? inputData, CancellationToken cancellationToken)
    {
        var config = JsonSerializer.Deserialize<Dictionary<string, object>>(node.NodeConfig ?? "{}");
        if (config == null)
        {
            throw new InvalidOperationException("LLM node must have config");
        }

            var serviceId = config.ContainsKey("serviceId") ? Convert.ToInt32(config["serviceId"]) : 1;
            var model = config.ContainsKey("model") ? config["model"]?.ToString() ?? "gpt-4-turbo" : "gpt-4-turbo";
            var prompt = config.ContainsKey("prompt") ? config["prompt"]?.ToString() ?? inputData ?? "" : inputData ?? "";

            var chatRequest = new ChatMessageRequestDto
            {
                Messages = new List<ChatMessageDto>
                {
                    new ChatMessageDto { Role = "user", Content = prompt }
                },
                Temperature = config.ContainsKey("temperature") ? Convert.ToDecimal(config["temperature"]) : 0.7m,
                MaxTokens = config.ContainsKey("maxTokens") ? Convert.ToInt32(config["maxTokens"]) : 2000
            };

            var response = await _aiProxyService.SendChatMessageAsync(serviceId, model, chatRequest, cancellationToken);
        return response.Content;
    }

    private async Task<string?> ExecuteToolNodeAsync(WorkflowNode node, string? inputData, CancellationToken cancellationToken)
    {
        var config = JsonSerializer.Deserialize<Dictionary<string, object>>(node.NodeConfig ?? "{}");
        if (config == null || !config.ContainsKey("toolId"))
        {
            throw new InvalidOperationException("Tool node must have toolId in config");
        }

        var toolId = Convert.ToInt32(config["toolId"]);
        var request = new ExecuteToolRequestDto { InputData = inputData };
        var execution = await _toolExecutionService.ExecuteToolAsync(toolId, request);
        return execution.OutputData;
    }

    private async Task<string?> ExecuteConditionNodeAsync(WorkflowNode node, string? inputData, CancellationToken cancellationToken)
    {
        var config = JsonSerializer.Deserialize<Dictionary<string, object>>(node.NodeConfig ?? "{}");
        if (config == null || !config.ContainsKey("condition"))
        {
            throw new InvalidOperationException("Condition node must have condition in config");
        }

        // 간단한 조건 평가 (실제로는 더 복잡한 로직 필요)
        var condition = config["condition"].ToString() ?? "";
        // 여기서는 단순히 입력 데이터를 그대로 반환
        return inputData;
    }

    private async Task<string?> ExecuteDataTransformNodeAsync(WorkflowNode node, string? inputData, CancellationToken cancellationToken)
    {
        var config = JsonSerializer.Deserialize<Dictionary<string, object>>(node.NodeConfig ?? "{}");
        // 데이터 변환 로직 (간단한 구현)
        return inputData;
    }
}
