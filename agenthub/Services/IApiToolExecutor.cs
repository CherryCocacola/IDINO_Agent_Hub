namespace AIAgentManagement.Services;

public interface IApiToolExecutor
{
    Task<string> ExecuteAsync(string config, string? inputData);
}
