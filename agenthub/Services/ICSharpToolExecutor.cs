namespace AIAgentManagement.Services;

public interface ICSharpToolExecutor
{
    Task<string> ExecuteAsync(string code, string? inputData);
}
