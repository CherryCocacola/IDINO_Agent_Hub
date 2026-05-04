using System.Text.Json;
using Microsoft.CodeAnalysis;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.Emit;
using System.Reflection;
using System.Runtime.Loader;
using System.Text;

namespace AIAgentManagement.Services;

public class CSharpToolExecutor : ICSharpToolExecutor
{
    private readonly ILogger<CSharpToolExecutor> _logger;
    private const int MaxExecutionTimeMs = 30000; // 30초
    private const long MaxMemoryBytes = 100 * 1024 * 1024; // 100MB

    public CSharpToolExecutor(ILogger<CSharpToolExecutor> logger)
    {
        _logger = logger;
    }

    public async Task<string> ExecuteAsync(string code, string? inputData)
    {
        try
        {
            // 기본 클래스 템플릿에 사용자 코드 삽입
            var fullCode = $@"
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;

public class ToolExecutor
{{
    public static string Execute(string inputJson)
    {{
        try
        {{
            // 사용자 코드
            {code}
            
            return ""{{}}""success"": true}}"";
        }}
        catch (Exception ex)
        {{
            return $""{{{{""success"": false, ""error"": ""{{JsonSerializer.Serialize(ex.Message)}}""}}}}"";
        }}
    }}
}}";

            // 코드 컴파일
            var syntaxTree = CSharpSyntaxTree.ParseText(fullCode);
            var references = new MetadataReference[]
            {
                MetadataReference.CreateFromFile(typeof(object).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(Console).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(System.Linq.Enumerable).Assembly.Location),
                MetadataReference.CreateFromFile(typeof(JsonSerializer).Assembly.Location),
                MetadataReference.CreateFromFile(Assembly.Load("System.Runtime").Location),
                MetadataReference.CreateFromFile(Assembly.Load("netstandard").Location)
            };

            var compilation = CSharpCompilation.Create(
                "ToolAssembly",
                new[] { syntaxTree },
                references,
                new CSharpCompilationOptions(OutputKind.DynamicallyLinkedLibrary));

            using var ms = new MemoryStream();
            var emitResult = compilation.Emit(ms);

            if (!emitResult.Success)
            {
                var errors = string.Join("\n", emitResult.Diagnostics
                    .Where(d => d.Severity == DiagnosticSeverity.Error)
                    .Select(d => d.GetMessage()));
                throw new InvalidOperationException($"Compilation failed: {errors}");
            }

            ms.Seek(0, SeekOrigin.Begin);

            // 어셈블리 로드 및 실행
            var assembly = AssemblyLoadContext.Default.LoadFromStream(ms);
            var type = assembly.GetType("ToolExecutor");
            var method = type?.GetMethod("Execute", BindingFlags.Public | BindingFlags.Static);

            if (method == null)
            {
                throw new InvalidOperationException("Execute method not found");
            }

            // 실행 (타임아웃 설정)
            var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(MaxExecutionTimeMs));
            var task = Task.Run(() => method.Invoke(null, new object[] { inputData ?? "{}" }), cts.Token);

            try
            {
                var result = await task;
                return result?.ToString() ?? "{}";
            }
            catch (OperationCanceledException)
            {
                throw new TimeoutException($"Tool execution exceeded maximum time limit of {MaxExecutionTimeMs}ms");
            }
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error executing C# tool");
            return JsonSerializer.Serialize(new { success = false, error = ex.Message });
        }
    }
}
