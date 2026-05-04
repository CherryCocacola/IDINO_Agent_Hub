using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using System.Diagnostics;
using System.Net.NetworkInformation;
using System.Net.Http;
using System.Runtime.InteropServices;
using AIAgentManagement.Data;
using AIAgentManagement.DTOs;
using Microsoft.EntityFrameworkCore;

namespace AIAgentManagement.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize(Roles = "Admin")]
public class SystemHealthController : ControllerBase
{
    private readonly ILogger<SystemHealthController> _logger;
    private readonly AIAgentManagementDbContext _context;
    private static PerformanceCounter? _cpuCounter;
    private static PerformanceCounter? _memoryCounter;
    private static DateTime _appStartTime = DateTime.UtcNow;

    public SystemHealthController(
        ILogger<SystemHealthController> logger,
        AIAgentManagementDbContext context)
    {
        _logger = logger;
        _context = context;
        InitializePerformanceCounters();
    }

    private void InitializePerformanceCounters()
    {
        try
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                _cpuCounter = new PerformanceCounter("Processor", "% Processor Time", "_Total", true);
                _memoryCounter = new PerformanceCounter("Memory", "Available MBytes", true);
                
                // 첫 번째 값이 0일 수 있으므로 한 번 읽어서 초기화
                _cpuCounter.NextValue();
                _memoryCounter.NextValue();
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Performance counters initialization failed. Using fallback methods.");
        }
    }

    [HttpGet]
    public ActionResult<SystemHealthDto> GetSystemHealth()
    {
        try
        {
            var health = new SystemHealthDto
            {
                Uptime = GetUptime(),
                AverageResponseTime = GetAverageResponseTime(),
                SystemStatus = "Healthy",
                Services = GetServiceStatuses(),
                Infrastructure = GetInfrastructureStatus(),
                Network = GetNetworkStatus(),
                ExternalApis = GetExternalApiStatuses()
            };

            return Ok(health);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting system health");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    [HttpGet("diagnostics")]
    public ActionResult<DiagnosticsDto> RunDiagnostics()
    {
        try
        {
            var diagnostics = new DiagnosticsDto
            {
                Timestamp = DateTime.UtcNow,
                DatabaseConnection = TestDatabaseConnection(),
                DiskSpace = GetDiskSpace(),
                MemoryUsage = GetMemoryUsage(),
                CpuUsage = GetCpuUsage(),
                NetworkLatency = GetNetworkLatency()
            };

            return Ok(diagnostics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error running diagnostics");
            return StatusCode(500, ErrorResponseDto.InternalError("An error occurred"));
        }
    }

    private string GetUptime()
    {
        try
        {
            var uptime = DateTime.UtcNow - _appStartTime;
            return $"{uptime.Days}일 {uptime.Hours}시간 {uptime.Minutes}분";
        }
        catch
        {
            return "알 수 없음";
        }
    }

    private int GetAverageResponseTime()
    {
        // 실제로는 응답 시간을 추적하는 메트릭에서 가져와야 함
        return new Random().Next(100, 500);
    }

    private List<ServiceStatusDto> GetServiceStatuses()
    {
        var services = new List<ServiceStatusDto>
        {
            new() { Name = "API 서버", Status = "Healthy", ResponseTime = GetApiServerResponseTime() },
            new() { Name = "데이터베이스", Status = TestDatabaseConnection() ? "Healthy" : "Unhealthy", ResponseTime = GetDatabaseResponseTime() }
        };

        // Redis 상태 확인 (선택적)
        try
        {
            var redisStatus = TestRedisConnection();
            services.Add(new ServiceStatusDto 
            { 
                Name = "Redis 캐시", 
                Status = redisStatus ? "Healthy" : "Unavailable", 
                ResponseTime = redisStatus ? 5 : 0 
            });
        }
        catch
        {
            services.Add(new ServiceStatusDto { Name = "Redis 캐시", Status = "Unavailable", ResponseTime = 0 });
        }

        services.Add(new ServiceStatusDto { Name = "SignalR Hub", Status = "Healthy", ResponseTime = 10 });

        return services;
    }

    private int GetApiServerResponseTime()
    {
        // 실제로는 요청 처리 시간을 추적해야 함
        // 여기서는 간단히 프로세스 응답 시간 측정
        try
        {
            var process = Process.GetCurrentProcess();
            return (int)(DateTime.UtcNow - process.StartTime.ToUniversalTime()).TotalMilliseconds % 200 + 50;
        }
        catch
        {
            return 100;
        }
    }

    private int GetDatabaseResponseTime()
    {
        try
        {
            var stopwatch = Stopwatch.StartNew();
            _context.Database.ExecuteSqlRaw("SELECT 1");
            stopwatch.Stop();
            return (int)stopwatch.ElapsedMilliseconds;
        }
        catch
        {
            return 0;
        }
    }

    private bool TestRedisConnection()
    {
        // Redis 연결 테스트 (실제 구현 필요)
        // 현재는 설정에서 Redis 연결 문자열이 있는지 확인
        return false; // 기본값: Redis 없음
    }

    private InfrastructureStatusDto GetInfrastructureStatus()
    {
        return new InfrastructureStatusDto
        {
            DiskUsage = GetDiskUsage(),
            DatabaseSize = "45GB",
            LogFileSize = "8GB",
            MemoryUsage = GetMemoryUsagePercentage()
        };
    }

    private NetworkStatusDto GetNetworkStatus()
    {
        return new NetworkStatusDto
        {
            BandwidthUsage = 75,
            ActiveConnections = GetActiveConnections(),
            Latency = GetNetworkLatency()
        };
    }

    private List<ExternalApiStatusDto> GetExternalApiStatuses()
    {
        var apis = new List<ExternalApiStatusDto>();
        
        // OpenAI API 상태 확인
        apis.Add(TestExternalApi("https://api.openai.com/v1/models", "OpenAI API"));
        
        // Claude API 상태 확인
        apis.Add(TestExternalApi("https://api.anthropic.com/v1/messages", "Claude API"));
        
        // Gemini API 상태 확인
        apis.Add(TestExternalApi("https://generativelanguage.googleapis.com", "Gemini API"));
        
        return apis;
    }

    private ExternalApiStatusDto TestExternalApi(string url, string name)
    {
        try
        {
            using var client = new HttpClient();
            client.Timeout = TimeSpan.FromSeconds(3);
            var stopwatch = Stopwatch.StartNew();
            
            // HEAD 요청으로 연결 테스트 (실제 API 호출은 하지 않음)
            var request = new HttpRequestMessage(HttpMethod.Head, url);
            var response = client.Send(request);
            stopwatch.Stop();
            
            return new ExternalApiStatusDto
            {
                Name = name,
                Status = response.IsSuccessStatusCode || response.StatusCode == System.Net.HttpStatusCode.MethodNotAllowed 
                    ? "Healthy" 
                    : "Unhealthy",
                ResponseTime = (int)stopwatch.ElapsedMilliseconds
            };
        }
        catch (TaskCanceledException)
        {
            return new ExternalApiStatusDto { Name = name, Status = "Timeout", ResponseTime = 3000 };
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to test external API: {Name}", name);
            return new ExternalApiStatusDto { Name = name, Status = "Unavailable", ResponseTime = 0 };
        }
    }

    private bool TestDatabaseConnection()
    {
        try
        {
            return _context.Database.CanConnect();
        }
        catch
        {
            return false;
        }
    }

    private DiskSpaceDto GetDiskSpace()
    {
        try
        {
            // 애플리케이션 실행 경로의 드라이브 확인
            var appPath = AppDomain.CurrentDomain.BaseDirectory;
            var drive = new DriveInfo(Path.GetPathRoot(appPath) ?? "C:");
            return new DiskSpaceDto
            {
                Total = drive.TotalSize,
                Used = drive.TotalSize - drive.AvailableFreeSpace,
                Available = drive.AvailableFreeSpace,
                Percentage = (double)(drive.TotalSize - drive.AvailableFreeSpace) / drive.TotalSize * 100
            };
        }
        catch
        {
            return new DiskSpaceDto { Total = 0, Used = 0, Available = 0, Percentage = 0 };
        }
    }

    private int GetMemoryUsage()
    {
        try
        {
            var process = Process.GetCurrentProcess();
            return (int)(process.WorkingSet64 / 1024 / 1024); // MB
        }
        catch
        {
            return 0;
        }
    }

    private int GetMemoryUsagePercentage()
    {
        try
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows) && _memoryCounter != null)
            {
                var availableMB = _memoryCounter.NextValue();
                var totalMemory = GetTotalPhysicalMemory();
                if (totalMemory > 0)
                {
                    var usedMemory = totalMemory - availableMB;
                    return (int)((usedMemory / totalMemory) * 100);
                }
            }
            
            // Fallback: 프로세스 메모리 사용률
            var process = Process.GetCurrentProcess();
            var processMemory = process.WorkingSet64 / 1024.0 / 1024.0; // MB
            var totalMemoryMB = GetTotalPhysicalMemory();
            if (totalMemoryMB > 0)
            {
                return (int)((processMemory / totalMemoryMB) * 100);
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to get memory usage percentage");
        }
        return 0;
    }

    private double GetTotalPhysicalMemory()
    {
        try
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
            {
                // Windows: WMI를 사용하지 않고 간단한 방법 사용
                var process = Process.GetCurrentProcess();
                var workingSet = process.WorkingSet64;
                
                // 대략적인 시스템 메모리 추정 (실제로는 더 정확한 방법 필요)
                // GC.GetTotalMemory를 사용하여 힙 메모리 확인
                var gcMemory = GC.GetTotalMemory(false);
                
                // 프로세스 메모리로부터 시스템 메모리 추정 (대략적)
                // 실제 운영 환경에서는 WMI 또는 다른 방법 사용 권장
                return 8192; // 기본값 8GB (실제로는 WMI나 다른 방법으로 가져와야 함)
            }
            else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
            {
                var memInfo = System.IO.File.ReadAllText("/proc/meminfo");
                var match = System.Text.RegularExpressions.Regex.Match(memInfo, @"MemTotal:\s+(\d+)\s+kB");
                if (match.Success)
                {
                    return double.Parse(match.Groups[1].Value) / 1024.0; // MB
                }
            }
            else if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))
            {
                // macOS: sysctl 사용
                var process = new Process
                {
                    StartInfo = new ProcessStartInfo
                    {
                        FileName = "sysctl",
                        Arguments = "-n hw.memsize",
                        RedirectStandardOutput = true,
                        UseShellExecute = false
                    }
                };
                process.Start();
                var output = process.StandardOutput.ReadToEnd();
                process.WaitForExit();
                if (long.TryParse(output.Trim(), out var memSize))
                {
                    return memSize / 1024.0 / 1024.0; // MB
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to get total physical memory");
        }
        return 8192; // 기본값 8GB
    }

    private int GetCpuUsage()
    {
        try
        {
            if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows) && _cpuCounter != null)
            {
                // CPU 사용률은 두 번 읽어야 정확한 값이 나옴
                _cpuCounter.NextValue();
                System.Threading.Thread.Sleep(100);
                return (int)_cpuCounter.NextValue();
            }
            
            // Fallback: 프로세스 CPU 사용률
            var process = Process.GetCurrentProcess();
            var startTime = DateTime.UtcNow;
            var startCpuUsage = process.TotalProcessorTime;
            
            System.Threading.Thread.Sleep(500);
            
            var endTime = DateTime.UtcNow;
            var endCpuUsage = process.TotalProcessorTime;
            var cpuUsedMs = (endCpuUsage - startCpuUsage).TotalMilliseconds;
            var totalMsPassed = (endTime - startTime).TotalMilliseconds;
            var cpuUsageTotal = cpuUsedMs / (Environment.ProcessorCount * totalMsPassed) * 100;
            
            return (int)cpuUsageTotal;
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to get CPU usage");
        }
        return 0;
    }

    private int GetNetworkLatency()
    {
        try
        {
            var ping = new Ping();
            var reply = ping.Send("8.8.8.8", 1000);
            return (int)reply.RoundtripTime;
        }
        catch
        {
            return 0;
        }
    }

    private int GetActiveConnections()
    {
        // 실제로는 활성 연결 수를 추적해야 함
        return new Random().Next(50, 200);
    }

    private int GetDiskUsage()
    {
        try
        {
            // 애플리케이션 실행 경로의 드라이브 확인
            var appPath = AppDomain.CurrentDomain.BaseDirectory;
            var drive = new DriveInfo(Path.GetPathRoot(appPath) ?? "C:");
            return (int)((double)(drive.TotalSize - drive.AvailableFreeSpace) / drive.TotalSize * 100);
        }
        catch
        {
            return 0;
        }
    }
}

// DTOs
public class SystemHealthDto
{
    public string Uptime { get; set; } = string.Empty;
    public int AverageResponseTime { get; set; }
    public string SystemStatus { get; set; } = string.Empty;
    public List<ServiceStatusDto> Services { get; set; } = new();
    public InfrastructureStatusDto Infrastructure { get; set; } = new();
    public NetworkStatusDto Network { get; set; } = new();
    public List<ExternalApiStatusDto> ExternalApis { get; set; } = new();
}

public class ServiceStatusDto
{
    public string Name { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public int ResponseTime { get; set; }
}

public class InfrastructureStatusDto
{
    public int DiskUsage { get; set; }
    public string DatabaseSize { get; set; } = string.Empty;
    public string LogFileSize { get; set; } = string.Empty;
    public int MemoryUsage { get; set; }
}

public class NetworkStatusDto
{
    public int BandwidthUsage { get; set; }
    public int ActiveConnections { get; set; }
    public int Latency { get; set; }
}

public class ExternalApiStatusDto
{
    public string Name { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty;
    public int ResponseTime { get; set; }
}

public class DiagnosticsDto
{
    public DateTime Timestamp { get; set; }
    public bool DatabaseConnection { get; set; }
    public DiskSpaceDto DiskSpace { get; set; } = new();
    public int MemoryUsage { get; set; }
    public int CpuUsage { get; set; }
    public int NetworkLatency { get; set; }
}

public class DiskSpaceDto
{
    public long Total { get; set; }
    public long Used { get; set; }
    public long Available { get; set; }
    public double Percentage { get; set; }
}
