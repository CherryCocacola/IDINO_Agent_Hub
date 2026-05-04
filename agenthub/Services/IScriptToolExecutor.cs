namespace AIAgentManagement.Services;

public interface IScriptToolExecutor
{
    Task<string> ExecuteAsync(string language, string code, string? inputData);
}
