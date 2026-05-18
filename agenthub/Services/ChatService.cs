using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using AIAgentManagement.Utils;
using AIAgentManagement.Exceptions;
using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Http;
using System.Collections.Concurrent;
using System.Runtime.CompilerServices;
using System.Text;

namespace AIAgentManagement.Services;

public class ChatService : IChatService
{
    // 동시 요청 시 대화 중복 생성 방지 (userId+agentId별 락)
    private static readonly ConcurrentDictionary<string, SemaphoreSlim> _convLocks = new();
    private readonly AIAgentManagementDbContext _context;
    private readonly IAiProxyService _aiProxyService;
    private readonly IQuotaService _quotaService;
    private readonly IBannedWordService _bannedWordService;
    private readonly IPiiDetectionService _piiDetectionService;
    private readonly IHttpContextAccessor _httpContextAccessor;
    private readonly CachingService _cachingService;
    private readonly ILogger<ChatService> _logger;
    // Phase 5.2 — Hybrid 라우팅 결정 엔진(LlmRouting="Hybrid" Agent 만 사용).
    // 옵셔널 주입으로 Phase 5.1 단위 테스트 호환성을 보존한다.
    private readonly IHybridRouter? _hybridRouter;

    public ChatService(
        AIAgentManagementDbContext context,
        IAiProxyService aiProxyService,
        IQuotaService quotaService,
        IBannedWordService bannedWordService,
        IPiiDetectionService piiDetectionService,
        IHttpContextAccessor httpContextAccessor,
        CachingService cachingService,
        ILogger<ChatService> logger,
        IHybridRouter? hybridRouter = null)
    {
        _context = context;
        _aiProxyService = aiProxyService;
        _quotaService = quotaService;
        _bannedWordService = bannedWordService;
        _piiDetectionService = piiDetectionService;
        _httpContextAccessor = httpContextAccessor;
        _cachingService = cachingService;
        _logger = logger;
        _hybridRouter = hybridRouter;
    }

    public async Task<List<ConversationDto>> GetConversationsAsync(int userId, bool? isArchived = null)
    {
        var query = _context.ChatConversations
            .AsNoTracking()
            .Include(c => c.ApiService)
            .Include(c => c.Agent)
            .Where(c => c.UserId == userId)
            .AsQueryable();

        if (isArchived.HasValue)
        {
            query = query.Where(c => c.IsArchived == isArchived.Value);
        }

        var conversations = await query
            .OrderByDescending(c => c.IsPinned)
            .ThenByDescending(c => c.LastMessageAt ?? c.CreatedAt)
            .ToListAsync();

        return conversations.Select(c => new ConversationDto
        {
            ConversationId = c.ConversationId,
            UserId = c.UserId,
            AgentId = c.AgentId,
            AgentName = c.Agent?.AgentName,
            ServiceId = c.ServiceId,
            ServiceName = c.ApiService?.ServiceName ?? "Unknown Service",
            Title = c.Title,
            Model = c.Model,
            Temperature = c.Temperature,
            MaxTokens = c.MaxTokens,
            MessageCount = c.MessageCount,
            TotalTokens = c.TotalTokens,
            TotalCost = c.TotalCost,
            LastMessageAt = c.LastMessageAt,
            IsArchived = c.IsArchived,
            IsPinned = c.IsPinned,
            Language = c.Language,
            EnableRag = c.EnableRag,
            EnableWebSearch = c.EnableWebSearch,
            CreatedAt = c.CreatedAt,
            UpdatedAt = c.UpdatedAt
        }).ToList();
    }

    public async Task<ConversationDto?> GetConversationByIdAsync(int conversationId, int userId)
    {
        var conversation = await _context.ChatConversations
            .AsNoTracking()
            .Include(c => c.ApiService)
            .Include(c => c.Agent)
            .FirstOrDefaultAsync(c => c.ConversationId == conversationId && c.UserId == userId);

        if (conversation == null) return null;

        return new ConversationDto
        {
            ConversationId = conversation.ConversationId,
            UserId = conversation.UserId,
            AgentId = conversation.AgentId,
            AgentName = conversation.Agent?.AgentName,
            ServiceId = conversation.ServiceId,
            ServiceName = conversation.ApiService.ServiceName,
            Title = conversation.Title,
            Model = conversation.Model,
            Temperature = conversation.Temperature,
            MaxTokens = conversation.MaxTokens,
            MessageCount = conversation.MessageCount,
            TotalTokens = conversation.TotalTokens,
            TotalCost = conversation.TotalCost,
            LastMessageAt = conversation.LastMessageAt,
            IsArchived = conversation.IsArchived,
            IsPinned = conversation.IsPinned,
            Language = conversation.Language,
            EnableRag = conversation.EnableRag,
            EnableWebSearch = conversation.EnableWebSearch,
            CreatedAt = conversation.CreatedAt,
            UpdatedAt = conversation.UpdatedAt
        };
    }

    public async Task<ConversationDto> CreateConversationAsync(CreateConversationRequestDto request, int userId)
    {
        // AgentId 가 제공되면 Agent 메타에서 ServiceId/Model/Temperature/MaxTokens/SystemPrompt 의 기본값을 보충.
        // SendDirectMessageAsync 등 다른 ChatService 메서드와 동일한 패턴(line 454-464). 둘 다 null 이면 400.
        if (request.AgentId.HasValue)
        {
            var agent = await _context.Agents
                .AsNoTracking()
                .FirstOrDefaultAsync(a => a.AgentId == request.AgentId.Value);

            if (agent == null)
            {
                throw new ArgumentException(
                    $"AgentId={request.AgentId.Value} 에 해당하는 에이전트를 찾을 수 없습니다.");
            }

            request.ServiceId ??= agent.ServiceId;
            request.Model ??= agent.DefaultModel;
            request.Temperature ??= agent.Temperature;
            request.MaxTokens ??= agent.MaxTokens;
            request.SystemPrompt ??= agent.SystemPrompt;
        }

        if (!request.ServiceId.HasValue || request.ServiceId.Value <= 0)
        {
            throw new ArgumentException(
                "ServiceId 또는 AgentId 중 하나는 반드시 제공되어야 합니다.");
        }

        var conversation = new Models.ChatConversation
        {
            UserId = userId,
            AgentId = request.AgentId,
            ServiceId = request.ServiceId.Value,
            Title = request.Title ?? "New Conversation",
            Model = request.Model,
            Temperature = request.Temperature,
            MaxTokens = request.MaxTokens,
            SystemPrompt = request.SystemPrompt,
            Language = request.Language ?? "auto",
            MessageCount = 0,
            TotalTokens = 0,
            TotalCost = 0,
            IsArchived = false,
            IsPinned = false,
            CreatedAt = DateTime.UtcNow,
            UpdatedAt = DateTime.UtcNow
        };

        _context.ChatConversations.Add(conversation);
        await _context.SaveChangesAsync();

        return await GetConversationByIdAsync(conversation.ConversationId, userId)
            ?? throw new InvalidOperationException("생성된 대화를 다시 조회하지 못했습니다.");
    }

    public async Task<ConversationDto?> UpdateConversationAsync(int conversationId, UpdateConversationRequestDto request, int userId)
    {
        var conversation = await _context.ChatConversations
            .FirstOrDefaultAsync(c => c.ConversationId == conversationId && c.UserId == userId);

        if (conversation == null) return null;

        conversation.Title = request.Title ?? conversation.Title;
        conversation.IsPinned = request.IsPinned ?? conversation.IsPinned;
        conversation.UpdatedAt = DateTime.UtcNow;

        await _context.SaveChangesAsync();
        return await GetConversationByIdAsync(conversationId, userId);
    }

    public async Task<bool> DeleteConversationAsync(int conversationId, int userId)
    {
        var conversation = await _context.ChatConversations
            .FirstOrDefaultAsync(c => c.ConversationId == conversationId && c.UserId == userId);

        if (conversation == null) return false;

        // 트랙 #97-post6 (2026-05-18) — 멀티채팅 이전 대화 삭제 결함 fix.
        //
        // 기존 결함: ApiUsages.ConversationId FK 가 RESTRICT 정책이라
        //   ChatConversations 삭제 시 PostgresException 23503 발생 → HTTP 500.
        //   사용자는 "삭제 안 됨" 으로 인식. UI 는 confirm 후 silent 실패.
        //
        // fix 정책: ApiUsage 는 사용량/비용 감사 기록이므로 보존 가치 있음.
        //   → ConversationId 만 NULL 로 nullify (Usage 자체는 보존, 어느 대화에서 발생했는지만 잊음).
        //   ChatMessages 는 대화의 일부이므로 conversation 과 함께 cascade 삭제.
        //
        // 트랜잭션 안에서 처리 — 중간 실패 시 전부 롤백.
        using var tx = await _context.Database.BeginTransactionAsync();
        try
        {
            // 1) ApiUsages.ConversationId = NULL (Usage 행은 보존, FK 위반 해소)
            var usages = await _context.ApiUsages
                .Where(u => u.ConversationId == conversationId)
                .ToListAsync();
            foreach (var u in usages)
            {
                u.ConversationId = null;
            }

            // 2) ChatMessages 는 대화의 본문 — 같이 삭제 (FK cascade 가 없다면 명시적으로)
            var messages = await _context.ChatMessages
                .Where(m => m.ConversationId == conversationId)
                .ToListAsync();
            if (messages.Count > 0)
            {
                _context.ChatMessages.RemoveRange(messages);
            }

            // 3) Conversation 본체 삭제
            _context.ChatConversations.Remove(conversation);

            await _context.SaveChangesAsync();
            await tx.CommitAsync();
            return true;
        }
        catch
        {
            await tx.RollbackAsync();
            throw;
        }
    }

    public async Task<List<ChatMessageDto>> GetMessagesAsync(int conversationId, int userId)
    {
        var conversation = await _context.ChatConversations
            .AsNoTracking()
            .FirstOrDefaultAsync(c => c.ConversationId == conversationId && c.UserId == userId);

        if (conversation == null) return new List<ChatMessageDto>();

        var messages = await _context.ChatMessages
            .AsNoTracking()
            .Where(m => m.ConversationId == conversationId)
            .OrderBy(m => m.CreatedAt)
            .ToListAsync();

        return messages.Select(m => new ChatMessageDto
        {
            MessageId = (int)m.MessageId,
            ConversationId = m.ConversationId,
            Role = m.Role,
            Content = m.Content,
            Attachments = m.Attachments, // 이미지 URL 목록 (JSON 문자열)
            TokensUsed = m.TokensUsed,
            Model = m.Model,
            FinishReason = m.FinishReason,
            CreatedAt = m.CreatedAt
        }).ToList();
    }

    public async Task<ChatMessageDto> SendMessageAsync(int conversationId, SendMessageRequestDto request, int userId)
    {
        var conversation = await _context.ChatConversations
            .Include(c => c.Agent)
            .FirstOrDefaultAsync(c => c.ConversationId == conversationId && c.UserId == userId);

        if (conversation == null)
        {
            throw new InvalidOperationException("Conversation not found");
        }

        // Check quota
        var quotaCheck = await _quotaService.CheckQuotaAsync(userId, conversation.ServiceId);
        if (!quotaCheck.CanUse)
        {
            throw new InvalidOperationException($"Quota exceeded: {quotaCheck.Message}");
        }

        // Check banned words
        var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(request.Message, conversation.AgentId);
        if (bannedWordCheck.IsBlocked)
        {
            throw new BannedWordException(bannedWordCheck.BlockedWords);
        }

        // Check and handle PII (Personal Identifiable Information)
        var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(conversation.AgentId);
        var messageToProcess = request.Message;
        
        if (piiSettings.Enabled)
        {
            var piiResult = await _piiDetectionService.DetectPiiAsync(request.Message, piiSettings.DetectionTypes);
            
            if (piiResult.HasPii)
            {
                if (piiSettings.Mode == "Block")
                {
                    var detectedTypes = piiResult.DetectedItems.Select(i => PiiTypeHelper.GetPiiTypeName(i.Type)).Distinct().ToList();
                    
                    // 로깅
                    await LogPiiDetectionAsync(userId, conversation.AgentId, conversationId, piiResult, "Block", _httpContextAccessor.HttpContext?.Connection?.RemoteIpAddress?.ToString());
                    
                    throw new PiiDetectionException(piiResult, detectedTypes);
                }
                else if (piiSettings.Mode == "Mask")
                {
                    // 마스킹 처리된 메시지 사용
                    messageToProcess = piiResult.MaskedMessage;
                    _logger.LogInformation("PII detected and masked in message. AgentId: {AgentId}, Types: {Types}", 
                        conversation.AgentId, string.Join(", ", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                    
                    // 로깅
                    await LogPiiDetectionAsync(userId, conversation.AgentId, conversationId, piiResult, "Mask", _httpContextAccessor.HttpContext?.Connection?.RemoteIpAddress?.ToString());
                }
            }
        }

        // H3(5-3) — 첨부 이미지를 사용자 메시지의 Attachments(JSON) 컬럼에 저장하여
        // 이후 페이지 재진입/대화 재로드 시에도 thumbnails 가 보존되도록 한다.
        // 저장 형식: 이미지 URL 목록(JSON string[]) — GetMessagesAsync 의 기존 로더와 호환.
        string? attachmentsJsonForDb = null;
        var imageAttachments = request.Attachments?
            .Where(a => string.Equals(a.Type, "image_url", StringComparison.OrdinalIgnoreCase)
                        && !string.IsNullOrWhiteSpace(a.ImageUrl))
            .ToList();
        if (imageAttachments != null && imageAttachments.Count > 0)
        {
            var imageUrls = imageAttachments.Select(a => a.ImageUrl!).ToList();
            attachmentsJsonForDb = System.Text.Json.JsonSerializer.Serialize(imageUrls);
        }

        // Save user message (마스킹된 메시지 저장)
        var userMessage = new Models.ChatMessage
        {
            ConversationId = conversationId,
            Role = "user",
            Content = messageToProcess, // 마스킹된 메시지 사용
            Attachments = attachmentsJsonForDb, // 이미지 URL 목록(JSON) — 첨부가 있으면 보존
            CreatedAt = DateTime.UtcNow
        };
        _context.ChatMessages.Add(userMessage);
        await _context.SaveChangesAsync();

        // Prepare AI request
        // context window 초과 및 토큰 폭증 방지를 위해 최근 30개 메시지만 사용
        const int historyLimit = 30;
        var chatMessages = await _context.ChatMessages
            .Where(m => m.ConversationId == conversationId)
            .OrderByDescending(m => m.CreatedAt)
            .Take(historyLimit)
            .OrderBy(m => m.CreatedAt)
            .ToListAsync();

        var messages = chatMessages.Select(m => new ChatMessageDto
        {
            Role = m.Role,
            Content = m.Content
        }).ToList();

        // H3(5-3) — 마지막 user 메시지(방금 저장한 것)에 멀티모달 Contents 결합.
        // OpenAI/Claude/Gemini 등 vision 분기는 AiProxyService 가 Contents 를 보면 멀티모달 payload 로 전환한다.
        if (request.Attachments != null && request.Attachments.Count > 0)
        {
            var lastUserDto = messages.LastOrDefault(m => m.Role == "user");
            if (lastUserDto != null)
            {
                var contents = new List<MessageContentDto>();
                // 텍스트 부분(원본 마스킹된 메시지)을 명시적으로 첫 번째 part 로 추가
                if (!string.IsNullOrWhiteSpace(lastUserDto.Content))
                {
                    contents.Add(new MessageContentDto
                    {
                        Type = "text",
                        Text = lastUserDto.Content
                    });
                }
                // 첨부 항목을 그대로 부착(image_url / audio_url / file 모두 허용)
                foreach (var att in request.Attachments)
                {
                    if (string.IsNullOrWhiteSpace(att.Type)) continue;
                    contents.Add(att);
                }
                lastUserDto.Contents = contents;
                // Content 는 그대로 두어 텍스트만 보는 분기(예: 일부 비-vision 폴백)도 정상 동작.

                _logger.LogInformation("멀티모달 첨부 적용: ConversationId={ConversationId}, ImageCount={ImageCount}, OtherCount={OtherCount}",
                    conversationId,
                    request.Attachments.Count(a => string.Equals(a.Type, "image_url", StringComparison.OrdinalIgnoreCase)),
                    request.Attachments.Count(a => !string.Equals(a.Type, "image_url", StringComparison.OrdinalIgnoreCase)));
            }
        }

        // Add system prompt if exists
        if (!string.IsNullOrEmpty(conversation.SystemPrompt))
        {
            messages.Insert(0, new ChatMessageDto
            {
                Role = "system",
                Content = conversation.SystemPrompt
            });
        }

        // 언어 설정: 요청에서 받거나 기존 대화의 언어 사용
        var language = request.Language ?? conversation.Language ?? "auto";
        if (request.Language != null && request.Language != conversation.Language)
        {
            conversation.Language = request.Language;
        }

        // Agent의 EnableRag 확인 및 RAG 활성화
        var enableRag = request.EnableRag ?? conversation.EnableRag;
        if (conversation.Agent != null && conversation.Agent.EnableRag && request.EnableRag != false)
        {
            // Agent에 RAG가 활성화되어 있고, 사용자가 명시적으로 비활성화하지 않은 경우
            enableRag = true;
        }

        var chatRequest = new ChatMessageRequestDto
        {
            Messages = messages,
            Temperature = conversation.Temperature,
            MaxTokens = conversation.MaxTokens,
            Stream = request.Stream ?? false,
            EnableWebSearch = request.EnableWebSearch ?? conversation.EnableWebSearch,
            EnableRag = enableRag,
            RagTopK = request.RagTopK,
            Language = language,
            UserId = userId,
            AgentId = conversation.Agent?.EnableRag == true && enableRag ? conversation.Agent.AgentId : null
        };

        var startTime = DateTime.UtcNow;

        // Call AI service
        var aiResponse = await _aiProxyService.SendChatMessageAsync(
            conversation.ServiceId,
            conversation.Model ?? "gpt-4-turbo",
            chatRequest
        );

        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        aiResponse.ResponseTime = responseTime;

        // Calculate cost
        var cost = await _aiProxyService.CalculateCostAsync(
            conversation.ServiceId,
            conversation.Model ?? "gpt-4-turbo",
            aiResponse.PromptTokens,
            aiResponse.CompletionTokens
        );
        aiResponse.Cost = cost;

        // Save assistant message
        var assistantMessage = new Models.ChatMessage
        {
            ConversationId = conversationId,
            Role = "assistant",
            Content = aiResponse.Content,
            TokensUsed = aiResponse.TotalTokens,
            Model = aiResponse.Model,
            FinishReason = aiResponse.FinishReason,
            CreatedAt = DateTime.UtcNow
        };
        
        // Gemini 3 Pro Image 편집 응답의 이미지들을 Attachments에 저장
        if (aiResponse.ImageUrls != null && aiResponse.ImageUrls.Count > 0)
        {
            var attachments = aiResponse.ImageUrls.Select((url, index) => new
            {
                type = "image",
                url = url,
                name = $"edited-image-{index + 1}.png"
            }).ToList();
            
            assistantMessage.Attachments = System.Text.Json.JsonSerializer.Serialize(attachments);
        }
        
        _context.ChatMessages.Add(assistantMessage);

        // Update conversation - MessageCount는 실제 저장된 메시지 개수로 계산
        // user 메시지는 이미 저장되었고, assistant 메시지를 추가하므로 실제 메시지 개수 업데이트
        var totalMessageCount = await _context.ChatMessages
            .Where(m => m.ConversationId == conversationId)
            .CountAsync() + 1; // +1 for assistant message just added
        
        conversation.MessageCount = totalMessageCount;
        conversation.TotalTokens += aiResponse.TotalTokens;
        conversation.TotalCost += cost;
        conversation.LastMessageAt = DateTime.UtcNow;
        conversation.UpdatedAt = DateTime.UtcNow;

        // Save API usage - 모든 API 호출에 대해 기록 (DATABASE_DESIGN.md 참고)
        var apiUsage = new Models.ApiUsage
        {
            UserId = userId,
            ServiceId = conversation.ServiceId,
            ConversationId = conversationId,
            Model = aiResponse.Model,
            TokensUsed = aiResponse.TotalTokens,
            RequestCost = cost,
            RequestTime = startTime,
            ResponseTime = responseTime,
            StatusCode = 200,
            Prompt = messageToProcess.Length > 500 ? messageToProcess[..500] : messageToProcess,
            CreatedAt = DateTime.UtcNow
        };
        _context.ApiUsages.Add(apiUsage);

        // Update quota
        await _quotaService.RecordUsageAsync(userId, conversation.ServiceId, aiResponse.TotalTokens, cost);

        // 모든 변경사항을 한 번에 저장 (트랜잭션 보장)
        await _context.SaveChangesAsync();

        return new ChatMessageDto
        {
            MessageId = (int)assistantMessage.MessageId,
            ConversationId = assistantMessage.ConversationId,
            Role = assistantMessage.Role,
            Content = assistantMessage.Content,
            TokensUsed = assistantMessage.TokensUsed,
            Model = assistantMessage.Model,
            FinishReason = assistantMessage.FinishReason,
            CreatedAt = assistantMessage.CreatedAt
        };
    }

    public async Task<bool> ArchiveConversationAsync(int conversationId, int userId, bool archive)
    {
        var conversation = await _context.ChatConversations
            .FirstOrDefaultAsync(c => c.ConversationId == conversationId && c.UserId == userId);

        if (conversation == null) return false;

        conversation.IsArchived = archive;
        conversation.UpdatedAt = DateTime.UtcNow;
        await _context.SaveChangesAsync();

        return true;
    }

    public async Task<DirectSendMessageResponseDto> SendDirectMessageAsync(DirectSendMessageRequestDto request, int userId)
    {
        // Agent가 있으면 Agent 정보 가져오기
        Models.Agent? agent = null;
        if (request.AgentId.HasValue)
        {
            agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(a => a.AgentId == request.AgentId.Value);

            if (agent != null && request.ServiceId == null)
            {
                request.ServiceId = agent.ServiceId;
            }
        }

        if (!request.ServiceId.HasValue)
        {
            throw new InvalidOperationException("ServiceId is required");
        }

        // Phase 5.2 — Agent.LlmRouting 평가 후 request.ServiceId 보정
        // (External=유지 / Internal=nexus / Hybrid=HybridRouter 결정)
        await ResolveServiceIdAsync(agent, request, CancellationToken.None);

        // Quota 체크
        var quotaCheck = await _quotaService.CheckQuotaAsync(userId, request.ServiceId.Value);
        if (!quotaCheck.CanUse)
        {
            throw new InvalidOperationException($"Quota exceeded: {quotaCheck.Message}");
        }

        // 사용자 메시지 추출: 이번 요청에서 보낸 마지막 사용자 메시지만 금칙어/개인정보 검사 (이전 대화 히스토리는 제외)
        var userMessages = request.Messages?.Where(m => m.Role == "user").ToList() ?? new List<ChatMessageItemDto>();
        var lastUserMessage = userMessages.LastOrDefault();
        if (lastUserMessage != null && !string.IsNullOrWhiteSpace(lastUserMessage.Content))
        {
            var contentToCheck = lastUserMessage.Content;

            // 금칙어 검사 (마지막 사용자 메시지만 검사 → 금칙어 오류 후 다른 메시지 보내면 정상 진행)
            var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(contentToCheck, request.AgentId);
            if (bannedWordCheck.IsBlocked)
            {
            throw new BannedWordException(bannedWordCheck.BlockedWords);
            }

            // Check and handle PII (마지막 사용자 메시지만 검사)
            var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(request.AgentId);
            if (piiSettings.Enabled)
            {
                var piiResult = await _piiDetectionService.DetectPiiAsync(contentToCheck, piiSettings.DetectionTypes);

                if (piiResult.HasPii)
                {
                    if (piiSettings.Mode == "Block")
                    {
                        var detectedTypes = piiResult.DetectedItems.Select(i => PiiTypeHelper.GetPiiTypeName(i.Type)).Distinct().ToList();
                        
                        // 로깅
                        await LogPiiDetectionAsync(userId, request.AgentId, null, piiResult, "Block", _httpContextAccessor.HttpContext?.Connection?.RemoteIpAddress?.ToString());
                        
                        throw new PiiDetectionException(piiResult, detectedTypes);
                    }
                    else if (piiSettings.Mode == "Mask")
                    {
                        lastUserMessage.Content = piiResult.MaskedMessage;
                        _logger.LogInformation("PII detected and masked in direct message. AgentId: {AgentId}, Types: {Types}",
                            request.AgentId, string.Join(", ", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                    }
                }
            }
        }

        // Conversation 찾기 또는 생성 (Agent가 있으면)
        Models.ChatConversation? conversation = null;
        int? conversationId = null;
        
        if (request.AgentId.HasValue)
        {
            // 1) conversationId가 요청에 있으면 해당 대화 사용 (연속 질문 시 동일 세션 유지)
            if (request.ConversationId.HasValue)
            {
                conversation = await _context.ChatConversations
                    .Include(c => c.ApiService)
                    .FirstOrDefaultAsync(c => 
                        c.ConversationId == request.ConversationId.Value && 
                        c.UserId == userId && 
                        c.AgentId == request.AgentId.Value && 
                        !c.IsArchived);
                if (conversation != null)
                {
                    conversationId = conversation.ConversationId;
                }
            }
            
            // 2) conversationId 없거나 검증 실패 시: 찾기 또는 생성 (동시 요청 시 락으로 중복 생성 방지)
            if (conversation == null)
            {
                var lockKey = $"{userId}_{request.AgentId.Value}";
                var semaphore = _convLocks.GetOrAdd(lockKey, _ => new SemaphoreSlim(1, 1));
                await semaphore.WaitAsync();
                try
                {
                    // 락 획득 후 다시 확인 (다른 요청이 이미 생성했을 수 있음)
                    conversation = await _context.ChatConversations
                        .Include(c => c.ApiService)
                        .Where(c => c.UserId == userId && c.AgentId == request.AgentId.Value && !c.IsArchived)
                        .OrderByDescending(c => c.CreatedAt)
                        .FirstOrDefaultAsync();
                    
                    if (conversation == null)
                    {
                        conversation = new Models.ChatConversation
                        {
                            UserId = userId,
                            AgentId = request.AgentId,
                            ServiceId = request.ServiceId.Value,
                            Title = agent?.AgentName ?? "New Chat",
                            Model = request.Model ?? agent?.ApiService?.DefaultModel ?? "gpt-4-turbo",
                            Temperature = request.Temperature ?? agent?.Temperature ?? 0.7m,
                            MaxTokens = request.MaxTokens ?? agent?.MaxTokens ?? 4096,
                            SystemPrompt = agent?.SystemPrompt,
                            Language = request.Language ?? "auto",
                            EnableRag = request.EnableRag ?? false,
                            EnableWebSearch = request.EnableWebSearch ?? false,
                            MessageCount = 0,
                            TotalTokens = 0,
                            TotalCost = 0,
                            IsArchived = false,
                            IsPinned = false,
                            CreatedAt = DateTime.UtcNow,
                            UpdatedAt = DateTime.UtcNow
                        };
                        _context.ChatConversations.Add(conversation);
                        await _context.SaveChangesAsync();
                    }
                    else
                    {
                        // 기존 대화가 있으면 설정 업데이트
                        if (!string.IsNullOrEmpty(request.Language))
                        {
                            conversation.Language = request.Language;
                        }
                        if (request.EnableRag.HasValue)
                        {
                            conversation.EnableRag = request.EnableRag.Value;
                        }
                        if (request.EnableWebSearch.HasValue)
                        {
                            conversation.EnableWebSearch = request.EnableWebSearch.Value;
                        }
                    }
                    conversationId = conversation.ConversationId;
                }
                finally
                {
                    semaphore.Release();
                }
            }
        }

        // 언어 설정: 요청에서 받거나 기존 대화의 언어 사용
        var language = request.Language ?? conversation?.Language ?? "auto";

        // Agent의 EnableRag 확인 및 RAG 활성화
        var enableRag = request.EnableRag ?? false;
        if (agent != null && agent.EnableRag && request.EnableRag != false)
        {
            // Agent에 RAG가 활성화되어 있고, 사용자가 명시적으로 비활성화하지 않은 경우
            enableRag = true;
        }

        // AI 요청 준비 - 멀티모달 지원
        var chatRequest = new ChatMessageRequestDto
        {
            Messages = (request.Messages ?? new List<ChatMessageItemDto>()).Select(m => new ChatMessageDto
            {
                Role = m.Role,
                Content = m.Content,
                Contents = m.Contents
            }).ToList(),
            Temperature = request.Temperature ?? conversation?.Temperature ?? 0.7m,
            MaxTokens = request.MaxTokens ?? conversation?.MaxTokens ?? 4096,
            Stream = request.Stream ?? false,
            EnableWebSearch = request.EnableWebSearch ?? false,
            EnableRag = enableRag,
            RagTopK = request.RagTopK,
            Language = language,
            UserId = userId,
            AgentId = agent?.EnableRag == true && enableRag && request.DocumentIds == null ? agent.AgentId : null,
            DocumentIds = request.DocumentIds, // 사용자가 선택한 문서 ID 목록
            EnableDeepResearch = request.EnableDeepResearch ?? false,
            EnableDeepThinking = request.EnableDeepThinking ?? false,
            ThinkingMode = request.ThinkingMode
        };
        
        _logger.LogInformation("Chat request prepared. EnableRag: {EnableRag}, DocumentIds: {DocumentIds}, AgentId: {AgentId}", 
            chatRequest.EnableRag,
            chatRequest.DocumentIds != null ? string.Join(", ", chatRequest.DocumentIds) : "null",
            chatRequest.AgentId);

        // Agent의 system prompt 추가
        if (agent != null && !string.IsNullOrEmpty(agent.SystemPrompt))
        {
            var systemMessage = chatRequest.Messages.FirstOrDefault(m => m.Role == "system");
            if (systemMessage == null)
            {
                chatRequest.Messages.Insert(0, new ChatMessageDto
                {
                    Role = "system",
                    Content = agent.SystemPrompt
                });
            }
            else
            {
                systemMessage.Content = agent.SystemPrompt;
            }
        }

        var startTime = DateTime.UtcNow;
        var model = request.Model ?? conversation?.Model ?? agent?.ApiService?.DefaultModel ?? "gpt-4-turbo";

        // ── 응답 캐싱 (동일 질문 재사용) ──────────────────────────────────────
        // RAG·웹검색·멀티모달이 없는 단순 텍스트 질문만 캐싱합니다.
        var canCache = !(chatRequest.EnableRag || chatRequest.EnableWebSearch || chatRequest.EnableDeepResearch)
                       && chatRequest.Messages.All(m => m.Contents == null || m.Contents.Count == 0);

        string? cacheKey = null;
        if (canCache && request.AgentId.HasValue)
        {
            // 캐시 키: agentId + 모델 + 전체 메시지 내용의 해시
            var messagesText = string.Concat(
                chatRequest.Messages.Select(m => $"{m.Role}:{m.Content}"));
            var hash = Convert.ToHexString(
                System.Security.Cryptography.SHA256.HashData(
                    System.Text.Encoding.UTF8.GetBytes(messagesText)));
            cacheKey = $"chat:resp:{request.AgentId.Value}:{model}:{hash[..16]}";

            var cached = await _cachingService.GetAsync<AiResponseDto>(cacheKey);
            if (cached != null)
            {
                _logger.LogInformation("응답 캐시 히트: AgentId={AgentId}, Key={Key}", request.AgentId.Value, cacheKey);
                cached.ResponseTime = 0; // 캐시에서 즉시 반환
                // 캐시 히트 시에는 DB 저장 없이 바로 반환
                return new DirectSendMessageResponseDto
                {
                    MessageId      = 0,
                    ConversationId = conversationId,
                    Content        = cached.Content,
                    Model          = cached.Model,
                    TokensUsed     = cached.TotalTokens,
                    Cost           = 0, // 캐시 사용 시 비용 0
                    ResponseTime   = 0,
                    Citations      = cached.Citations
                };
            }
        }

        // AI 서비스 호출 (실패 시 Fallback 모델로 자동 전환)
        AiResponseDto aiResponse;
        try
        {
            aiResponse = await _aiProxyService.SendChatMessageAsync(
                request.ServiceId.Value, model, chatRequest);
        }
        catch (HttpRequestException ex) when (
            ex.StatusCode == System.Net.HttpStatusCode.TooManyRequests ||
            ex.StatusCode == System.Net.HttpStatusCode.InternalServerError ||
            ex.StatusCode == System.Net.HttpStatusCode.ServiceUnavailable)
        {
            // Fallback 모델 결정: 요청에서 명시 → 기본 매핑 순으로 확인
            var fallbackModel = request.FallbackModel ?? GetDefaultFallbackModel(model);
            if (string.IsNullOrEmpty(fallbackModel) || fallbackModel == model)
                throw; // Fallback 없으면 원래 예외 그대로 전파

            _logger.LogWarning(
                "AI 모델 {Primary} 호출 실패 (HTTP {Status}), Fallback 모델 {Fallback}로 재시도합니다.",
                model, (int?)ex.StatusCode, fallbackModel);

            aiResponse = await _aiProxyService.SendChatMessageAsync(
                request.ServiceId.Value, fallbackModel, chatRequest);

            // Fallback 성공 시 실제 사용된 모델로 업데이트
            model = fallbackModel;
        }

        // ── 응답 캐시 저장 (5분 TTL) ──────────────────────────────────────────
        if (canCache && cacheKey != null)
        {
            try
            {
                await _cachingService.SetAsync(cacheKey, aiResponse, TimeSpan.FromMinutes(5));
            }
            catch (Exception cacheEx)
            {
                // 캐시 저장 실패는 무시 (메인 로직에 영향 없음)
                _logger.LogWarning(cacheEx, "응답 캐시 저장 실패: Key={Key}", cacheKey);
            }
        }

        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        aiResponse.ResponseTime = responseTime;

        // 비용 계산
        var cost = await _aiProxyService.CalculateCostAsync(
            request.ServiceId.Value,
            model,
            aiResponse.PromptTokens,
            aiResponse.CompletionTokens
        );
        aiResponse.Cost = cost;

        // Conversation이 있으면 저장
        if (conversation != null)
        {
            // 사용자 메시지 저장
            var userMessage = request.Messages?.LastOrDefault(m => m.Role == "user");
            if (userMessage != null)
            {
                var attachmentsJson = userMessage.Contents != null && userMessage.Contents.Count > 0
                    ? System.Text.Json.JsonSerializer.Serialize(userMessage.Contents)
                    : null;
                
                var dbUserMessage = new Models.ChatMessage
                {
                    ConversationId = conversation.ConversationId,
                    Role = "user",
                    Content = userMessage.Content ?? "",
                    Attachments = attachmentsJson,
                    CreatedAt = DateTime.UtcNow
                };
                _context.ChatMessages.Add(dbUserMessage);
            }

            // Assistant 메시지 저장
            var assistantMessage = new Models.ChatMessage
            {
                ConversationId = conversation.ConversationId,
                Role = "assistant",
                Content = aiResponse.Content,
                TokensUsed = aiResponse.TotalTokens,
                Model = aiResponse.Model,
                FinishReason = aiResponse.FinishReason,
                CreatedAt = DateTime.UtcNow
            };
            
            // Gemini 3 Pro Image 편집 응답의 이미지들을 Attachments에 저장
            if (aiResponse.ImageUrls != null && aiResponse.ImageUrls.Count > 0)
            {
                var attachments = aiResponse.ImageUrls.Select((url, index) => new
                {
                    type = "image",
                    url = url,
                    name = $"edited-image-{index + 1}.png"
                }).ToList();
                
                assistantMessage.Attachments = System.Text.Json.JsonSerializer.Serialize(attachments);
            }
            
            _context.ChatMessages.Add(assistantMessage);

            // Conversation 업데이트 - 실제 메시지 개수 계산
            var totalMessageCount = await _context.ChatMessages
                .Where(m => m.ConversationId == conversation.ConversationId)
                .CountAsync() + 1; // +1 for assistant message just added
            
            conversation.MessageCount = totalMessageCount;
            conversation.TotalTokens += aiResponse.TotalTokens;
            conversation.TotalCost += cost;
            conversation.LastMessageAt = DateTime.UtcNow;
            conversation.UpdatedAt = DateTime.UtcNow;
            // RAG 및 웹 검색 설정 업데이트
            if (request.EnableRag.HasValue)
            {
                conversation.EnableRag = request.EnableRag.Value;
            }
            if (request.EnableWebSearch.HasValue)
            {
                conversation.EnableWebSearch = request.EnableWebSearch.Value;
            }

            // API 사용량 기록 - 모든 API 호출에 대해 기록 (DATABASE_DESIGN.md 참고)
            var directPrompt = request.Messages?.LastOrDefault(m => m.Role == "user")?.Content;
            var apiUsage = new Models.ApiUsage
            {
                UserId = userId,
                ServiceId = request.ServiceId.Value,
                ConversationId = conversation.ConversationId,
                Model = aiResponse.Model,
                TokensUsed = aiResponse.TotalTokens,
                RequestCost = cost,
                RequestTime = startTime,
                ResponseTime = responseTime,
                StatusCode = 200,
                Prompt = directPrompt != null && directPrompt.Length > 500 ? directPrompt[..500] : directPrompt,
                CreatedAt = DateTime.UtcNow
            };
            _context.ApiUsages.Add(apiUsage);

            // 모든 변경사항을 한 번에 저장 (트랜잭션 보장)
            await _context.SaveChangesAsync();
        }
        else
        {
            // Conversation이 없으면 새로 생성하여 저장
            var firstUserMessage = request.Messages?.FirstOrDefault(m => m.Role == "user");
            var conversationTitle = firstUserMessage?.Content?.Length > 50 
                ? firstUserMessage.Content.Substring(0, 50) + "..." 
                : firstUserMessage?.Content ?? "새 대화";

            // Conversation 생성 (초기값 설정)
            var newConversation = new Models.ChatConversation
            {
                UserId = userId,
                AgentId = request.AgentId,
                ServiceId = request.ServiceId.Value,
                Title = conversationTitle,
                Model = model,
                Temperature = request.Temperature ?? 0.7m,
                MaxTokens = request.MaxTokens ?? 4096,
                SystemPrompt = agent?.SystemPrompt,
                Language = request.Language ?? "auto",
                EnableRag = request.EnableRag ?? false,
                EnableWebSearch = request.EnableWebSearch ?? false,
                MessageCount = 0, // 초기값, 메시지 저장 후 업데이트
                TotalTokens = 0, // 초기값, 메시지 저장 후 업데이트
                TotalCost = 0, // 초기값, 메시지 저장 후 업데이트
                LastMessageAt = null, // 초기값, 메시지 저장 후 업데이트
                IsArchived = false,
                IsPinned = false,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };
            _context.ChatConversations.Add(newConversation);
            await _context.SaveChangesAsync(); // ConversationId 생성

            // 메시지 저장
            var userMessage = request.Messages?.LastOrDefault(m => m.Role == "user");
            if (userMessage != null)
            {
                var dbUserMessage = new Models.ChatMessage
                {
                    ConversationId = newConversation.ConversationId,
                    Role = "user",
                    Content = userMessage.Content ?? "",
                    CreatedAt = DateTime.UtcNow
                };
                _context.ChatMessages.Add(dbUserMessage);
            }

            var assistantMessage = new Models.ChatMessage
            {
                ConversationId = newConversation.ConversationId,
                Role = "assistant",
                Content = aiResponse.Content,
                TokensUsed = aiResponse.TotalTokens,
                Model = aiResponse.Model,
                FinishReason = aiResponse.FinishReason,
                CreatedAt = DateTime.UtcNow
            };
            
            // Gemini 3 Pro Image 편집 응답의 이미지들을 Attachments에 저장
            if (aiResponse.ImageUrls != null && aiResponse.ImageUrls.Count > 0)
            {
                var attachments = aiResponse.ImageUrls.Select((url, index) => new
                {
                    type = "image",
                    url = url,
                    name = $"edited-image-{index + 1}.png"
                }).ToList();
                
                assistantMessage.Attachments = System.Text.Json.JsonSerializer.Serialize(attachments);
            }
            
            _context.ChatMessages.Add(assistantMessage);

            // Conversation 업데이트 - 실제 메시지 개수 및 통계 계산
            var savedMessageCount = await _context.ChatMessages
                .Where(m => m.ConversationId == newConversation.ConversationId)
                .CountAsync();
            
            newConversation.MessageCount = savedMessageCount;
            newConversation.TotalTokens = aiResponse.TotalTokens;
            newConversation.TotalCost = cost;
            newConversation.LastMessageAt = DateTime.UtcNow;
            newConversation.UpdatedAt = DateTime.UtcNow;
            // RAG 및 웹 검색 설정 업데이트
            if (request.EnableRag.HasValue)
            {
                newConversation.EnableRag = request.EnableRag.Value;
            }
            if (request.EnableWebSearch.HasValue)
            {
                newConversation.EnableWebSearch = request.EnableWebSearch.Value;
            }

            // API 사용량 기록 - 모든 API 호출에 대해 기록 (DATABASE_DESIGN.md 참고)
            var newDirectPrompt = request.Messages?.LastOrDefault(m => m.Role == "user")?.Content;
            var apiUsage = new Models.ApiUsage
            {
                UserId = userId,
                ServiceId = request.ServiceId.Value,
                ConversationId = newConversation.ConversationId,
                Model = aiResponse.Model,
                TokensUsed = aiResponse.TotalTokens,
                RequestCost = cost,
                RequestTime = startTime,
                ResponseTime = responseTime,
                StatusCode = 200,
                Prompt = newDirectPrompt != null && newDirectPrompt.Length > 500 ? newDirectPrompt[..500] : newDirectPrompt,
                CreatedAt = DateTime.UtcNow
            };
            _context.ApiUsages.Add(apiUsage);
            
            conversationId = newConversation.ConversationId;
            
            // 모든 변경사항을 한 번에 저장 (트랜잭션 보장)
            await _context.SaveChangesAsync();
        }

        // 할당량 업데이트
        await _quotaService.RecordUsageAsync(userId, request.ServiceId.Value, aiResponse.TotalTokens, cost);

        var lastMessage = conversation != null 
            ? await _context.ChatMessages
                .Where(m => m.ConversationId == conversation.ConversationId)
                .OrderByDescending(m => m.CreatedAt)
                .FirstOrDefaultAsync()
            : null;

        return new DirectSendMessageResponseDto
        {
            MessageId = lastMessage != null ? (int)lastMessage.MessageId : 0,
            ConversationId = conversationId,
            Content = aiResponse.Content,
            Model = aiResponse.Model,
            TokensUsed = aiResponse.TotalTokens,
            Cost = cost,
            ResponseTime = responseTime,
            Citations = aiResponse.Citations
        };
    }


    // ════════════════════════════════════════════════════════════════════════
    // 진짜 SSE 스트리밍 wrapper (TECHSPEC §15.4 / §16 C9 해소)
    // ════════════════════════════════════════════════════════════════════════
    public async IAsyncEnumerable<ChatChunk> SendDirectMessageStreamChunksAsync(
        DirectSendMessageRequestDto request,
        int userId,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // ── Agent 조회 + ServiceId 확정 ────────────────────────────────────────
        Models.Agent? agent = null;
        if (request.AgentId.HasValue)
        {
            agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(a => a.AgentId == request.AgentId.Value, cancellationToken);

            if (agent != null && request.ServiceId == null)
            {
                request.ServiceId = agent.ServiceId;
            }
        }

        if (!request.ServiceId.HasValue)
        {
            throw new InvalidOperationException("ServiceId is required");
        }

        // Phase 5.2 — Agent.LlmRouting 평가 후 request.ServiceId 보정
        await ResolveServiceIdAsync(agent, request, cancellationToken);

        // ── Quota 사전 체크 ────────────────────────────────────────────────────
        var quotaCheck = await _quotaService.CheckQuotaAsync(userId, request.ServiceId.Value);
        if (!quotaCheck.CanUse)
        {
            throw new InvalidOperationException($"Quota exceeded: {quotaCheck.Message}");
        }

        // ── 마지막 user 메시지에 한해 BannedWord + PII 검사 ─────────────────────
        var userMessages = request.Messages?.Where(m => m.Role == "user").ToList() ?? new List<ChatMessageItemDto>();
        var lastUserMessage = userMessages.LastOrDefault();
        if (lastUserMessage != null && !string.IsNullOrWhiteSpace(lastUserMessage.Content))
        {
            var contentToCheck = lastUserMessage.Content;

            var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(contentToCheck, request.AgentId);
            if (bannedWordCheck.IsBlocked)
            {
                throw new BannedWordException(bannedWordCheck.BlockedWords);
            }

            var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(request.AgentId);
            if (piiSettings.Enabled)
            {
                var piiResult = await _piiDetectionService.DetectPiiAsync(contentToCheck, piiSettings.DetectionTypes);
                if (piiResult.HasPii)
                {
                    if (piiSettings.Mode == "Block")
                    {
                        var detectedTypes = piiResult.DetectedItems.Select(i => PiiTypeHelper.GetPiiTypeName(i.Type)).Distinct().ToList();
                        await LogPiiDetectionAsync(userId, request.AgentId, null, piiResult, "Block",
                            _httpContextAccessor.HttpContext?.Connection?.RemoteIpAddress?.ToString());
                        throw new PiiDetectionException(piiResult, detectedTypes);
                    }
                    if (piiSettings.Mode == "Mask")
                    {
                        lastUserMessage.Content = piiResult.MaskedMessage;
                        _logger.LogInformation("PII detected and masked in stream message. AgentId: {AgentId}, Types: {Types}",
                            request.AgentId, string.Join(", ", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                    }
                }
            }
        }

        // ── 대화 컨테이너 결정/생성 (비스트리밍 흐름과 동일) ──────────────────────
        Models.ChatConversation? conversation = null;
        int? conversationId = null;

        if (request.AgentId.HasValue)
        {
            if (request.ConversationId.HasValue)
            {
                conversation = await _context.ChatConversations
                    .Include(c => c.ApiService)
                    .FirstOrDefaultAsync(c =>
                        c.ConversationId == request.ConversationId.Value &&
                        c.UserId == userId &&
                        c.AgentId == request.AgentId.Value &&
                        !c.IsArchived, cancellationToken);
                if (conversation != null)
                {
                    conversationId = conversation.ConversationId;
                }
            }

            if (conversation == null)
            {
                var lockKey = $"{userId}_{request.AgentId.Value}";
                var semaphore = _convLocks.GetOrAdd(lockKey, _ => new SemaphoreSlim(1, 1));
                await semaphore.WaitAsync(cancellationToken);
                try
                {
                    conversation = await _context.ChatConversations
                        .Include(c => c.ApiService)
                        .Where(c => c.UserId == userId && c.AgentId == request.AgentId.Value && !c.IsArchived)
                        .OrderByDescending(c => c.CreatedAt)
                        .FirstOrDefaultAsync(cancellationToken);

                    if (conversation == null)
                    {
                        conversation = new Models.ChatConversation
                        {
                            UserId = userId,
                            AgentId = request.AgentId,
                            ServiceId = request.ServiceId.Value,
                            Title = agent?.AgentName ?? "New Chat",
                            Model = request.Model ?? agent?.ApiService?.DefaultModel ?? "gpt-4-turbo",
                            Temperature = request.Temperature ?? agent?.Temperature ?? 0.7m,
                            MaxTokens = request.MaxTokens ?? agent?.MaxTokens ?? 4096,
                            SystemPrompt = agent?.SystemPrompt,
                            Language = request.Language ?? "auto",
                            EnableRag = request.EnableRag ?? false,
                            EnableWebSearch = request.EnableWebSearch ?? false,
                            MessageCount = 0,
                            TotalTokens = 0,
                            TotalCost = 0,
                            IsArchived = false,
                            IsPinned = false,
                            CreatedAt = DateTime.UtcNow,
                            UpdatedAt = DateTime.UtcNow
                        };
                        _context.ChatConversations.Add(conversation);
                        await _context.SaveChangesAsync(cancellationToken);
                    }
                    conversationId = conversation.ConversationId;
                }
                finally
                {
                    semaphore.Release();
                }
            }
        }

        // ── ChatMessageRequestDto 변환 (Agent system prompt + RAG 플래그 반영) ───
        var language = request.Language ?? conversation?.Language ?? "auto";
        var enableRag = request.EnableRag ?? false;
        if (agent != null && agent.EnableRag && request.EnableRag != false) enableRag = true;

        var chatRequest = new ChatMessageRequestDto
        {
            Messages = (request.Messages ?? new List<ChatMessageItemDto>()).Select(m => new ChatMessageDto
            {
                Role = m.Role,
                Content = m.Content,
                Contents = m.Contents
            }).ToList(),
            Temperature = request.Temperature ?? conversation?.Temperature ?? 0.7m,
            MaxTokens = request.MaxTokens ?? conversation?.MaxTokens ?? 4096,
            Stream = true,
            EnableWebSearch = request.EnableWebSearch ?? false,
            EnableRag = enableRag,
            RagTopK = request.RagTopK,
            Language = language,
            UserId = userId,
            AgentId = agent?.EnableRag == true && enableRag && request.DocumentIds == null ? agent.AgentId : null,
            DocumentIds = request.DocumentIds,
            EnableDeepResearch = request.EnableDeepResearch ?? false,
            EnableDeepThinking = request.EnableDeepThinking ?? false,
            ThinkingMode = request.ThinkingMode
        };

        if (agent != null && !string.IsNullOrEmpty(agent.SystemPrompt))
        {
            var systemMessage = chatRequest.Messages.FirstOrDefault(m => m.Role == "system");
            if (systemMessage == null)
            {
                chatRequest.Messages.Insert(0, new ChatMessageDto { Role = "system", Content = agent.SystemPrompt });
            }
            else
            {
                systemMessage.Content = agent.SystemPrompt;
            }
        }

        var startTime = DateTime.UtcNow;
        var model = request.Model ?? conversation?.Model ?? agent?.ApiService?.DefaultModel ?? "gpt-4-turbo";

        // ── 진짜 SSE 스트리밍 ───────────────────────────────────────────────────
        var contentBuilder = new StringBuilder();
        int promptTokens = 0;
        int completionTokens = 0;
        int totalTokens = 0;
        string finishReason = "stop";

        await foreach (var chunk in _aiProxyService
            .SendChatMessageStreamChunksAsync(request.ServiceId.Value, model, chatRequest, cancellationToken)
            .WithCancellation(cancellationToken))
        {
            if (!string.IsNullOrEmpty(chunk.Content))
            {
                contentBuilder.Append(chunk.Content);
            }
            if (chunk.PromptTokens.HasValue || chunk.CompletionTokens.HasValue || chunk.TotalTokens.HasValue)
            {
                promptTokens = chunk.PromptTokens ?? promptTokens;
                completionTokens = chunk.CompletionTokens ?? completionTokens;
                totalTokens = chunk.TotalTokens ?? totalTokens;
            }
            if (!string.IsNullOrEmpty(chunk.FinishReason))
            {
                finishReason = chunk.FinishReason;
            }

            yield return chunk;
        }

        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        var fullContent = contentBuilder.ToString();

        // 토큰 정보가 누락된 경우(provider streaming 미지원 폴백 등) 보수적으로 0 처리
        var cost = await _aiProxyService.CalculateCostAsync(request.ServiceId.Value, model, promptTokens, completionTokens);

        // ── 메시지 / ApiUsage / Conversation 통계 영속화 ────────────────────────
        try
        {
            if (conversation != null)
            {
                var userMessage = request.Messages?.LastOrDefault(m => m.Role == "user");
                if (userMessage != null)
                {
                    var attachmentsJson = userMessage.Contents != null && userMessage.Contents.Count > 0
                        ? System.Text.Json.JsonSerializer.Serialize(userMessage.Contents)
                        : null;
                    _context.ChatMessages.Add(new Models.ChatMessage
                    {
                        ConversationId = conversation.ConversationId,
                        Role = "user",
                        Content = userMessage.Content ?? string.Empty,
                        Attachments = attachmentsJson,
                        CreatedAt = DateTime.UtcNow
                    });
                }

                _context.ChatMessages.Add(new Models.ChatMessage
                {
                    ConversationId = conversation.ConversationId,
                    Role = "assistant",
                    Content = fullContent,
                    TokensUsed = totalTokens,
                    Model = model,
                    FinishReason = finishReason,
                    CreatedAt = DateTime.UtcNow
                });

                var totalMessageCount = await _context.ChatMessages
                    .Where(m => m.ConversationId == conversation.ConversationId)
                    .CountAsync(cancellationToken) + 1;

                conversation.MessageCount = totalMessageCount;
                conversation.TotalTokens += totalTokens;
                conversation.TotalCost += cost;
                conversation.LastMessageAt = DateTime.UtcNow;
                conversation.UpdatedAt = DateTime.UtcNow;

                var directPrompt = request.Messages?.LastOrDefault(m => m.Role == "user")?.Content;
                _context.ApiUsages.Add(new Models.ApiUsage
                {
                    UserId = userId,
                    ServiceId = request.ServiceId.Value,
                    ConversationId = conversation.ConversationId,
                    Model = model,
                    TokensUsed = totalTokens,
                    RequestCost = cost,
                    RequestTime = startTime,
                    ResponseTime = responseTime,
                    StatusCode = 200,
                    Prompt = directPrompt != null && directPrompt.Length > 500 ? directPrompt[..500] : directPrompt,
                    CreatedAt = DateTime.UtcNow
                });

                await _context.SaveChangesAsync(cancellationToken);
            }

            // 할당량 차감 (마지막 usage chunk 기준)
            await _quotaService.RecordUsageAsync(userId, request.ServiceId.Value, totalTokens, cost);
        }
        catch (Exception ex)
        {
            // 영속화 실패는 사용자 경험에 영향을 주지 않도록 로그만 남기고 silently 종료
            // (이미 chunk는 사용자에게 모두 전달된 상태)
            _logger.LogError(ex, "Streaming 종료 후 메시지/사용량 영속화 실패. UserId: {UserId}, ServiceId: {ServiceId}, Model: {Model}",
                userId, request.ServiceId.Value, model);
        }
    }

    /// <summary>
    /// Vue UI 전용 진짜 SSE 스트리밍.
    /// SendDirectMessageStreamChunksAsync 와 동일한 정책(PII / BannedWord / Quota / Conversation lock / 영속화)을 따르되,
    /// 영속화 후 Vue UI 가 활용할 수 있도록 conversationId / messageId / model / cost 를 담은 meta 이벤트를
    /// 마지막에 yield 합니다.
    ///
    /// Phase 3.5b — 사용자 보고 "Vue UI에서 5~10초 대기 후 일괄 출력" 직접 해소.
    /// 기존 SendDirectMessageStreamChunksAsync (OpenAI 호환 전용) 와는 분리되어 있으며 코드 중복이 일부 존재합니다.
    /// Phase 5+ 에서 공통 streaming 코어 분리 리팩토링 예정.
    /// </summary>
    public async IAsyncEnumerable<ChatStreamEvent> SendDirectMessageStreamEventsAsync(
        DirectSendMessageRequestDto request,
        int userId,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        // ── Agent 조회 + ServiceId 확정 ────────────────────────────────────────
        Models.Agent? agent = null;
        if (request.AgentId.HasValue)
        {
            agent = await _context.Agents
                .Include(a => a.ApiService)
                .FirstOrDefaultAsync(a => a.AgentId == request.AgentId.Value, cancellationToken);

            if (agent != null && request.ServiceId == null)
            {
                request.ServiceId = agent.ServiceId;
            }
        }

        if (!request.ServiceId.HasValue)
        {
            throw new InvalidOperationException("ServiceId is required");
        }

        // Phase 5.2 — Agent.LlmRouting 평가 후 request.ServiceId 보정
        await ResolveServiceIdAsync(agent, request, cancellationToken);

        // ── Quota 사전 체크 ────────────────────────────────────────────────────
        var quotaCheck = await _quotaService.CheckQuotaAsync(userId, request.ServiceId.Value);
        if (!quotaCheck.CanUse)
        {
            throw new InvalidOperationException($"Quota exceeded: {quotaCheck.Message}");
        }

        // ── 마지막 user 메시지에 한해 BannedWord + PII 검사 ─────────────────────
        var userMessages = request.Messages?.Where(m => m.Role == "user").ToList() ?? new List<ChatMessageItemDto>();
        var lastUserMessage = userMessages.LastOrDefault();
        if (lastUserMessage != null && !string.IsNullOrWhiteSpace(lastUserMessage.Content))
        {
            var contentToCheck = lastUserMessage.Content;

            var bannedWordCheck = await _bannedWordService.CheckBannedWordsAsync(contentToCheck, request.AgentId);
            if (bannedWordCheck.IsBlocked)
            {
                throw new BannedWordException(bannedWordCheck.BlockedWords);
            }

            var piiSettings = await _piiDetectionService.GetAgentSettingsAsync(request.AgentId);
            if (piiSettings.Enabled)
            {
                var piiResult = await _piiDetectionService.DetectPiiAsync(contentToCheck, piiSettings.DetectionTypes);
                if (piiResult.HasPii)
                {
                    if (piiSettings.Mode == "Block")
                    {
                        var detectedTypes = piiResult.DetectedItems.Select(i => PiiTypeHelper.GetPiiTypeName(i.Type)).Distinct().ToList();
                        await LogPiiDetectionAsync(userId, request.AgentId, null, piiResult, "Block",
                            _httpContextAccessor.HttpContext?.Connection?.RemoteIpAddress?.ToString());
                        throw new PiiDetectionException(piiResult, detectedTypes);
                    }
                    if (piiSettings.Mode == "Mask")
                    {
                        lastUserMessage.Content = piiResult.MaskedMessage;
                        _logger.LogInformation("PII detected and masked in stream message. AgentId: {AgentId}, Types: {Types}",
                            request.AgentId, string.Join(", ", piiResult.DetectedItems.Select(i => i.Type).Distinct()));
                    }
                }
            }
        }

        // ── 대화 컨테이너 결정/생성 ─────────────────────────────────────────────
        Models.ChatConversation? conversation = null;

        if (request.AgentId.HasValue)
        {
            if (request.ConversationId.HasValue)
            {
                conversation = await _context.ChatConversations
                    .Include(c => c.ApiService)
                    .FirstOrDefaultAsync(c =>
                        c.ConversationId == request.ConversationId.Value &&
                        c.UserId == userId &&
                        c.AgentId == request.AgentId.Value &&
                        !c.IsArchived, cancellationToken);
            }

            if (conversation == null)
            {
                var lockKey = $"{userId}_{request.AgentId.Value}";
                var semaphore = _convLocks.GetOrAdd(lockKey, _ => new SemaphoreSlim(1, 1));
                await semaphore.WaitAsync(cancellationToken);
                try
                {
                    conversation = await _context.ChatConversations
                        .Include(c => c.ApiService)
                        .Where(c => c.UserId == userId && c.AgentId == request.AgentId.Value && !c.IsArchived)
                        .OrderByDescending(c => c.CreatedAt)
                        .FirstOrDefaultAsync(cancellationToken);

                    if (conversation == null)
                    {
                        conversation = new Models.ChatConversation
                        {
                            UserId = userId,
                            AgentId = request.AgentId,
                            ServiceId = request.ServiceId.Value,
                            Title = agent?.AgentName ?? "New Chat",
                            Model = request.Model ?? agent?.ApiService?.DefaultModel ?? "gpt-4-turbo",
                            Temperature = request.Temperature ?? agent?.Temperature ?? 0.7m,
                            MaxTokens = request.MaxTokens ?? agent?.MaxTokens ?? 4096,
                            SystemPrompt = agent?.SystemPrompt,
                            Language = request.Language ?? "auto",
                            EnableRag = request.EnableRag ?? false,
                            EnableWebSearch = request.EnableWebSearch ?? false,
                            MessageCount = 0,
                            TotalTokens = 0,
                            TotalCost = 0,
                            IsArchived = false,
                            IsPinned = false,
                            CreatedAt = DateTime.UtcNow,
                            UpdatedAt = DateTime.UtcNow
                        };
                        _context.ChatConversations.Add(conversation);
                        await _context.SaveChangesAsync(cancellationToken);
                    }
                }
                finally
                {
                    semaphore.Release();
                }
            }
        }

        // ── ChatMessageRequestDto 변환 ──────────────────────────────────────────
        var language = request.Language ?? conversation?.Language ?? "auto";
        var enableRag = request.EnableRag ?? false;
        if (agent != null && agent.EnableRag && request.EnableRag != false) enableRag = true;

        var chatRequest = new ChatMessageRequestDto
        {
            Messages = (request.Messages ?? new List<ChatMessageItemDto>()).Select(m => new ChatMessageDto
            {
                Role = m.Role,
                Content = m.Content,
                Contents = m.Contents
            }).ToList(),
            Temperature = request.Temperature ?? conversation?.Temperature ?? 0.7m,
            MaxTokens = request.MaxTokens ?? conversation?.MaxTokens ?? 4096,
            Stream = true,
            EnableWebSearch = request.EnableWebSearch ?? false,
            EnableRag = enableRag,
            RagTopK = request.RagTopK,
            Language = language,
            UserId = userId,
            AgentId = agent?.EnableRag == true && enableRag && request.DocumentIds == null ? agent.AgentId : null,
            DocumentIds = request.DocumentIds,
            EnableDeepResearch = request.EnableDeepResearch ?? false,
            EnableDeepThinking = request.EnableDeepThinking ?? false,
            ThinkingMode = request.ThinkingMode
        };

        if (agent != null && !string.IsNullOrEmpty(agent.SystemPrompt))
        {
            var systemMessage = chatRequest.Messages.FirstOrDefault(m => m.Role == "system");
            if (systemMessage == null)
            {
                chatRequest.Messages.Insert(0, new ChatMessageDto { Role = "system", Content = agent.SystemPrompt });
            }
            else
            {
                systemMessage.Content = agent.SystemPrompt;
            }
        }

        var startTime = DateTime.UtcNow;
        var model = request.Model ?? conversation?.Model ?? agent?.ApiService?.DefaultModel ?? "gpt-4-turbo";

        // ── 진짜 SSE 스트리밍 ───────────────────────────────────────────────────
        var contentBuilder = new StringBuilder();
        int promptTokens = 0;
        int completionTokens = 0;
        int totalTokens = 0;
        string finishReason = "stop";
        bool usageEmitted = false;

        await foreach (var chunk in _aiProxyService
            .SendChatMessageStreamChunksAsync(request.ServiceId.Value, model, chatRequest, cancellationToken)
            .WithCancellation(cancellationToken))
        {
            if (!string.IsNullOrEmpty(chunk.Content))
            {
                contentBuilder.Append(chunk.Content);
                yield return ChatStreamEvent.Delta(chunk.Content);
            }

            if (chunk.PromptTokens.HasValue || chunk.CompletionTokens.HasValue || chunk.TotalTokens.HasValue)
            {
                promptTokens = chunk.PromptTokens ?? promptTokens;
                completionTokens = chunk.CompletionTokens ?? completionTokens;
                totalTokens = chunk.TotalTokens ?? totalTokens;
            }
            if (!string.IsNullOrEmpty(chunk.FinishReason))
            {
                finishReason = chunk.FinishReason;
            }
        }

        var responseTime = (int)(DateTime.UtcNow - startTime).TotalMilliseconds;
        var fullContent = contentBuilder.ToString();
        var cost = await _aiProxyService.CalculateCostAsync(request.ServiceId.Value, model, promptTokens, completionTokens);

        // usage event — 영속화 전에 흘려보내 클라이언트가 비용/토큰을 즉시 표시 가능
        if (totalTokens > 0)
        {
            yield return ChatStreamEvent.UsageEvent(promptTokens, completionTokens, totalTokens, cost);
            usageEmitted = true;
        }

        // ── 메시지 / ApiUsage / Conversation 통계 영속화 ────────────────────────
        int? finalConversationId = conversation?.ConversationId;
        long? finalMessageId = null;

        try
        {
            if (conversation != null)
            {
                var userMessage = request.Messages?.LastOrDefault(m => m.Role == "user");
                if (userMessage != null)
                {
                    var attachmentsJson = userMessage.Contents != null && userMessage.Contents.Count > 0
                        ? System.Text.Json.JsonSerializer.Serialize(userMessage.Contents)
                        : null;
                    _context.ChatMessages.Add(new Models.ChatMessage
                    {
                        ConversationId = conversation.ConversationId,
                        Role = "user",
                        Content = userMessage.Content ?? string.Empty,
                        Attachments = attachmentsJson,
                        CreatedAt = DateTime.UtcNow
                    });
                }

                var assistantMessage = new Models.ChatMessage
                {
                    ConversationId = conversation.ConversationId,
                    Role = "assistant",
                    Content = fullContent,
                    TokensUsed = totalTokens,
                    Model = model,
                    FinishReason = finishReason,
                    CreatedAt = DateTime.UtcNow
                };
                _context.ChatMessages.Add(assistantMessage);

                var totalMessageCount = await _context.ChatMessages
                    .Where(m => m.ConversationId == conversation.ConversationId)
                    .CountAsync(cancellationToken) + 1;

                conversation.MessageCount = totalMessageCount;
                conversation.TotalTokens += totalTokens;
                conversation.TotalCost += cost;
                conversation.LastMessageAt = DateTime.UtcNow;
                conversation.UpdatedAt = DateTime.UtcNow;

                var directPrompt = request.Messages?.LastOrDefault(m => m.Role == "user")?.Content;
                _context.ApiUsages.Add(new Models.ApiUsage
                {
                    UserId = userId,
                    ServiceId = request.ServiceId.Value,
                    ConversationId = conversation.ConversationId,
                    Model = model,
                    TokensUsed = totalTokens,
                    RequestCost = cost,
                    RequestTime = startTime,
                    ResponseTime = responseTime,
                    StatusCode = 200,
                    Prompt = directPrompt != null && directPrompt.Length > 500 ? directPrompt[..500] : directPrompt,
                    CreatedAt = DateTime.UtcNow
                });

                await _context.SaveChangesAsync(cancellationToken);

                // SaveChanges 이후 EF가 IDENTITY를 채워줌
                finalMessageId = assistantMessage.MessageId;
            }

            // 할당량 차감
            await _quotaService.RecordUsageAsync(userId, request.ServiceId.Value, totalTokens, cost);
        }
        catch (Exception ex)
        {
            // 영속화 실패는 사용자 경험에 영향을 주지 않도록 로그만 남기고 계속 진행
            // (delta/usage chunk 는 이미 사용자에게 모두 전달된 상태)
            _logger.LogError(ex, "Streaming 종료 후 메시지/사용량 영속화 실패. UserId: {UserId}, ServiceId: {ServiceId}, Model: {Model}",
                userId, request.ServiceId.Value, model);
        }

        // ── meta event — 영속화 결과를 클라이언트에 전달 ───────────────────────
        // usage 가 0 토큰 폴백 등으로 미발행된 경우 meta 의 cost 필드로 동시 전달
        yield return ChatStreamEvent.Meta(
            conversationId: finalConversationId,
            messageId: finalMessageId,
            model: model,
            cost: usageEmitted ? null : cost);
    }

    private async Task LogPiiDetectionAsync(int userId, int? agentId, int? conversationId, PiiDetectionResult piiResult, string actionTaken, string? ipAddress)
    {
        try
        {
            // 각 감지된 항목에 대해 로그 생성 (원본 메시지 일부만 저장 - 보안)
            foreach (var item in piiResult.DetectedItems)
            {
                // 원본 메시지에서 해당 부분만 추출 (앞뒤 20자씩)
                var messagePreview = piiResult.MaskedMessage.Length > 100 
                    ? piiResult.MaskedMessage.Substring(0, 100) + "..."
                    : piiResult.MaskedMessage;

                var log = new Models.PiiDetectionLog
                {
                    UserId = userId,
                    AgentId = agentId,
                    ConversationId = conversationId,
                    DetectionType = item.Type,
                    OriginalMessage = $"[{item.Type}] {messagePreview}", // 타입과 메시지 일부만 저장
                    ActionTaken = actionTaken,
                    DetectedAt = DateTime.UtcNow,
                    IpAddress = ipAddress
                };

                _context.PiiDetectionLogs.Add(log);
            }

            await _context.SaveChangesAsync();
        }
        catch (Exception ex)
        {
            // 로깅 실패해도 메인 로직은 계속 진행
            _logger.LogError(ex, "Error logging PII detection. UserId: {UserId}, AgentId: {AgentId}", userId, agentId);
        }
    }

    // ════════════════════════════════════════════════════════════════════════
    // 모델 Fallback 기본 매핑
    // Primary 모델 실패 시 경량 모델로 자동 전환합니다.
    // ════════════════════════════════════════════════════════════════════════
    private static string? GetDefaultFallbackModel(string primaryModel) => primaryModel switch
    {
        // OpenAI
        "gpt-4o"                      => "gpt-4o-mini",
        "gpt-4o-2024-11-20"           => "gpt-4o-mini",
        "gpt-4-turbo"                 => "gpt-4o-mini",
        "gpt-4"                       => "gpt-3.5-turbo",
        "o1"                          => "gpt-4o-mini",
        "o1-mini"                     => "gpt-4o-mini",
        "o3-mini"                     => "gpt-4o-mini",

        // Claude
        "claude-opus-4-6"             => "claude-sonnet-4-6",
        "claude-sonnet-4-6"           => "claude-haiku-4-5-20251001",
        "claude-haiku-4-5-20251001"   => "gpt-4o-mini",

        // Mistral
        "mistral-large-latest"        => "mistral-small-latest",
        "mistral-medium-latest"       => "mistral-small-latest",

        // Gemini
        "gemini-2.0-pro"              => "gemini-2.0-flash",
        "gemini-1.5-pro"              => "gemini-1.5-flash",

        _                             => null  // 매핑 없으면 Fallback 사용 안 함
    };

    // ════════════════════════════════════════════════════════════════════════
    // Phase 5.2 — Agent.LlmRouting 평가 + Nexus 분기 (.claude/rules/architecture.md P3)
    //
    // 라우팅은 ChatService 의 책임이다. AiProxyService 는 god class(3,966 LOC) 라서
    // god class 안에 라우팅 결정까지 들이는 것은 H13(분해 트랙) 와 충돌. 라우팅 결정은
    // "어떤 ApiService 를 쓸 것인가" 이고, AiProxy 는 "선택된 ApiService 를 어떻게 호출하는가"
    // 만 책임진다.
    //
    // 동작:
    //   - LlmRouting="External" / null → request.ServiceId 그대로 (기존 동작 유지)
    //   - LlmRouting="Internal" → "nexus" ApiService 의 ServiceId 로 치환
    //   - LlmRouting="Hybrid" → IHybridRouter.DecideAsync 결과로 분기
    //
    // 호출자(SendDirectMessageAsync / SendDirectMessageStreamChunksAsync /
    //        SendDirectMessageStreamEventsAsync) 는 결정 전에 request.ServiceId 가
    // 채워져 있다고 가정하므로(Agent.ServiceId 폴백), 본 헬퍼는 in-place 로 request.ServiceId
    // 만 갱신한다(외부 시그니처 무변경).
    // ════════════════════════════════════════════════════════════════════════
    private async Task ResolveServiceIdAsync(
        Models.Agent? agent,
        DirectSendMessageRequestDto request,
        CancellationToken cancellationToken)
    {
        // Agent 미지정 또는 라우팅 없음 → 외부 폴백(기존 동작).
        if (agent == null || string.IsNullOrWhiteSpace(agent.LlmRouting))
        {
            return;
        }

        var routing = agent.LlmRouting.Trim();

        // External → 기존 ServiceId 유지.
        if (string.Equals(routing, "External", StringComparison.OrdinalIgnoreCase))
        {
            return;
        }

        // Internal → 무조건 nexus.
        if (string.Equals(routing, "Internal", StringComparison.OrdinalIgnoreCase))
        {
            await SwapToServiceCodeAsync("nexus", request, agent, "internal_routing", cancellationToken);
            return;
        }

        // Hybrid → HybridRouter 결정.
        if (string.Equals(routing, "Hybrid", StringComparison.OrdinalIgnoreCase))
        {
            if (_hybridRouter == null)
            {
                _logger.LogWarning(
                    "Agent {AgentId} 가 Hybrid 모드인데 HybridRouter 미주입 — External 폴백",
                    agent.AgentId);
                return;
            }

            // ChatMessageRequestDto 로 변환해 평가 — DTO 변환은 가벼운 메시지 매핑만.
            var pseudoRequest = new ChatMessageRequestDto
            {
                Messages = (request.Messages ?? new List<ChatMessageItemDto>())
                    .Select(m => new ChatMessageDto
                    {
                        Role = m.Role,
                        Content = m.Content,
                        Contents = m.Contents
                    }).ToList(),
                Temperature = request.Temperature ?? 0.7m,
                MaxTokens = request.MaxTokens ?? 4096,
                Language = request.Language,
            };

            var decision = await _hybridRouter.DecideAsync(agent, pseudoRequest, cancellationToken);
            _logger.LogInformation(
                "HybridRouter 결정: AgentId={AgentId}, Decision={Decision}, Reason={Reason}, Detail={Detail}",
                agent.AgentId, decision.Decision, decision.Reason, decision.Detail ?? "(none)");

            if (string.Equals(decision.Decision, "internal", StringComparison.OrdinalIgnoreCase))
            {
                await SwapToServiceCodeAsync("nexus", request, agent, decision.Reason, cancellationToken);
            }
            // External 결정은 기존 ServiceId 유지(Agent.ServiceId).
            return;
        }

        // 알 수 없는 LlmRouting 값 → 기존 동작 보존 + 경고.
        _logger.LogWarning(
            "Agent {AgentId} 의 LlmRouting 값 '{Routing}' 인식 불가 — External 폴백",
            agent.AgentId, routing);
    }

    /// <summary>request.ServiceId 를 주어진 ServiceCode 의 ApiService 로 치환.</summary>
    private async Task SwapToServiceCodeAsync(
        string targetServiceCode,
        DirectSendMessageRequestDto request,
        Models.Agent agent,
        string reason,
        CancellationToken cancellationToken)
    {
        var targetService = await _context.ApiServices
            .Where(s => s.ServiceCode == targetServiceCode && s.IsActive)
            .Select(s => new { s.ServiceId })
            .FirstOrDefaultAsync(cancellationToken);

        if (targetService == null)
        {
            _logger.LogWarning(
                "라우팅 결정 reason={Reason} 였으나 활성 ApiService '{ServiceCode}' 미존재 — Agent.ServiceId 유지. AgentId={AgentId}",
                reason, targetServiceCode, agent.AgentId);
            return;
        }

        var previousId = request.ServiceId;
        request.ServiceId = targetService.ServiceId;
        _logger.LogInformation(
            "라우팅 적용: AgentId={AgentId}, Reason={Reason}, ServiceId {Previous} → {New} (ServiceCode={Code})",
            agent.AgentId, reason, previousId, targetService.ServiceId, targetServiceCode);
    }
}
