using System.Text;
using System.Diagnostics;
using UglyToad.PdfPig;
using UglyToad.PdfPig.Content;
using ClosedXML.Excel;
using DocumentFormat.OpenXml.Packaging;
using DocumentFormat.OpenXml.Wordprocessing;
using CsvHelper;
using System.Globalization;
using Microsoft.Extensions.Configuration;

namespace AIAgentManagement.Services;

public class FileParsingService : IFileParsingService
{
    private readonly ILogger<FileParsingService> _logger;
    private readonly IConfiguration _configuration;

    public FileParsingService(ILogger<FileParsingService> logger, IConfiguration configuration)
    {
        _logger = logger;
        _configuration = configuration;
    }

    public bool CanParse(string fileName, string mimeType)
    {
        var extension = Path.GetExtension(fileName).ToLowerInvariant();
        var supportedExtensions = new[]
        {
            ".pdf", ".txt", ".csv", ".xls", ".xlsx", ".doc", ".docx", ".hwp", ".hwpx", ".ppt", ".pptx"
        };
        return supportedExtensions.Contains(extension);
    }

    public async Task<FileParseResult> ParseFileAsync(Stream fileStream, string fileName, string mimeType)
    {
        var extension = Path.GetExtension(fileName).ToLowerInvariant();

        try
        {
            return extension switch
            {
                ".pdf" => await ParsePdfAsync(fileStream),
                ".txt" => await ParseTextAsync(fileStream),
                ".csv" => await ParseCsvAsync(fileStream),
                ".xls" or ".xlsx" => await ParseExcelAsync(fileStream, extension),
                ".doc" or ".docx" => await ParseWordAsync(fileStream, extension),
                ".hwp" or ".hwpx" => await ParseHwpAsync(fileStream, extension),
                ".ppt" or ".pptx" => await ParsePptxAsync(fileStream, extension),
                _ => new FileParseResult
                {
                    IsSuccess = false,
                    ErrorMessage = $"Unsupported file type: {extension}",
                    FileType = extension
                }
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing file {FileName}", fileName);
            return new FileParseResult
            {
                IsSuccess = false,
                ErrorMessage = ex.Message,
                FileType = extension
            };
        }
    }

    private async Task<FileParseResult> ParsePdfAsync(Stream fileStream)
    {
        var content = new StringBuilder();
        var images = new List<string>();

        try
        {
            using var document = PdfDocument.Open(fileStream);
            foreach (Page page in document.GetPages())
            {
                content.AppendLine(page.Text);
            }

            return new FileParseResult
            {
                Content = content.ToString(),
                Images = images.Count > 0 ? images : null,
                FileType = "pdf",
                IsSuccess = true,
                Metadata = new Dictionary<string, object>
                {
                    { "PageCount", document.NumberOfPages },
                    { "Title", document.Information?.Title ?? "" },
                    { "Author", document.Information?.Author ?? "" }
                }
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing PDF");
            return new FileParseResult
            {
                IsSuccess = false,
                ErrorMessage = $"PDF parsing error: {ex.Message}",
                FileType = "pdf"
            };
        }
    }

    private async Task<FileParseResult> ParseTextAsync(Stream fileStream)
    {
        using var reader = new StreamReader(fileStream, Encoding.UTF8);
        var content = await reader.ReadToEndAsync();

        return new FileParseResult
        {
            Content = content,
            FileType = "txt",
            IsSuccess = true
        };
    }

    private async Task<FileParseResult> ParseCsvAsync(Stream fileStream)
    {
        var content = new StringBuilder();
        
        try
        {
            fileStream.Position = 0;
            using var reader = new StreamReader(fileStream, Encoding.UTF8);
            using var csv = new CsvReader(reader, CultureInfo.InvariantCulture);
            
            await csv.ReadAsync();
            csv.ReadHeader();
            var headers = csv.HeaderRecord ?? Array.Empty<string>();
            
            // Write headers
            content.AppendLine(string.Join(" | ", headers));
            content.AppendLine(new string('-', headers.Length * 20));
            
            // Write rows
            while (await csv.ReadAsync())
            {
                var row = new List<string>();
                foreach (var header in headers)
                {
                    row.Add(csv.GetField(header) ?? "");
                }
                content.AppendLine(string.Join(" | ", row));
            }

            return new FileParseResult
            {
                Content = content.ToString(),
                FileType = "csv",
                IsSuccess = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing CSV");
            return new FileParseResult
            {
                IsSuccess = false,
                ErrorMessage = $"CSV parsing error: {ex.Message}",
                FileType = "csv"
            };
        }
    }

    private async Task<FileParseResult> ParseExcelAsync(Stream fileStream, string extension)
    {
        var content = new StringBuilder();
        
        try
        {
            fileStream.Position = 0;
            using var workbook = new XLWorkbook(fileStream);
            
            foreach (var worksheet in workbook.Worksheets)
            {
                content.AppendLine($"=== Sheet: {worksheet.Name} ===");
                
                var usedRange = worksheet.RangeUsed();
                if (usedRange != null)
                {
                    foreach (var row in usedRange.Rows())
                    {
                        var rowData = new List<string>();
                        foreach (var cell in row.Cells())
                        {
                            var cellValue = cell.GetString();
                            rowData.Add(string.IsNullOrEmpty(cellValue) ? "" : cellValue);
                        }
                        if (rowData.Any(x => !string.IsNullOrEmpty(x)))
                        {
                            content.AppendLine(string.Join(" | ", rowData));
                        }
                    }
                }
                content.AppendLine();
            }

            return new FileParseResult
            {
                Content = content.ToString(),
                FileType = extension.Replace(".", ""),
                IsSuccess = true,
                Metadata = new Dictionary<string, object>
                {
                    { "SheetCount", workbook.Worksheets.Count }
                }
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing Excel");
            return new FileParseResult
            {
                IsSuccess = false,
                ErrorMessage = $"Excel parsing error: {ex.Message}",
                FileType = extension.Replace(".", "")
            };
        }
    }

    private async Task<FileParseResult> ParseWordAsync(Stream fileStream, string extension)
    {
        var content = new StringBuilder();
        
        try
        {
            fileStream.Position = 0;
            
            if (extension == ".docx")
            {
                using var wordDocument = WordprocessingDocument.Open(fileStream, false);
                var body = wordDocument.MainDocumentPart?.Document?.Body;
                
                if (body != null)
                {
                    foreach (var element in body.Elements())
                    {
                        if (element is Paragraph paragraph)
                        {
                            var paragraphText = paragraph.InnerText;
                            if (!string.IsNullOrWhiteSpace(paragraphText))
                            {
                                content.AppendLine(paragraphText);
                            }
                        }
                        else if (element is Table table)
                        {
                            foreach (var row in table.Elements<TableRow>())
                            {
                                var rowData = new List<string>();
                                foreach (var cell in row.Elements<TableCell>())
                                {
                                    rowData.Add(cell.InnerText.Trim());
                                }
                                if (rowData.Any(x => !string.IsNullOrEmpty(x)))
                                {
                                    content.AppendLine(string.Join(" | ", rowData));
                                }
                            }
                            content.AppendLine();
                        }
                    }
                }
            }
            else
            {
                // .doc 파일은 기본적으로 바이너리 형식이므로 텍스트 추출이 제한적
                // 실제 구현에서는 Aspose.Words 등 상용 라이브러리 필요
                return new FileParseResult
                {
                    IsSuccess = false,
                    ErrorMessage = ".doc 파일은 현재 지원되지 않습니다. .docx 형식으로 변환해주세요.",
                    FileType = "doc"
                };
            }

            return new FileParseResult
            {
                Content = content.ToString(),
                FileType = extension.Replace(".", ""),
                IsSuccess = true
            };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing Word document");
            return new FileParseResult
            {
                IsSuccess = false,
                ErrorMessage = $"Word parsing error: {ex.Message}",
                FileType = extension.Replace(".", "")
            };
        }
    }

    private async Task<FileParseResult> ParseHwpAsync(Stream fileStream, string extension)
    {
        try
        {
            // LibreOffice를 사용하여 HWP/HWPX를 PDF로 변환
            var pdfStream = await ConvertOfficeToPdfAsync(fileStream, extension);
            if (pdfStream == null)
            {
                return new FileParseResult
                {
                    IsSuccess = false,
                    ErrorMessage = "HWP/HWPX 파일을 PDF로 변환할 수 없습니다. LibreOffice가 설치되어 있는지 확인해주세요.",
                    FileType = extension.Replace(".", "")
                };
            }

            // 변환된 PDF를 파싱
            return await ParsePdfAsync(pdfStream);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing HWP/HWPX file");
            return new FileParseResult
            {
                IsSuccess = false,
                ErrorMessage = $"HWP/HWPX 파일 파싱 오류: {ex.Message}",
                FileType = extension.Replace(".", "")
            };
        }
    }

    private async Task<FileParseResult> ParsePptxAsync(Stream fileStream, string extension)
    {
        try
        {
            // LibreOffice를 사용하여 PPTX를 PDF로 변환
            var pdfStream = await ConvertOfficeToPdfAsync(fileStream, extension);
            if (pdfStream == null)
            {
                return new FileParseResult
                {
                    IsSuccess = false,
                    ErrorMessage = "PPTX 파일을 PDF로 변환할 수 없습니다. LibreOffice가 설치되어 있는지 확인해주세요.",
                    FileType = extension.Replace(".", "")
                };
            }

            // 변환된 PDF를 파싱
            return await ParsePdfAsync(pdfStream);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error parsing PPTX file");
            return new FileParseResult
            {
                IsSuccess = false,
                ErrorMessage = $"PPTX 파일 파싱 오류: {ex.Message}",
                FileType = extension.Replace(".", "")
            };
        }
    }

    private async Task<Stream?> ConvertOfficeToPdfAsync(Stream fileStream, string extension)
    {
        var tempDir = Path.Combine(Path.GetTempPath(), Guid.NewGuid().ToString());
        Directory.CreateDirectory(tempDir);

        try
        {
            // 임시 파일 저장
            var tempInputFile = Path.Combine(tempDir, $"input{extension}");
            using (var fileStreamCopy = new FileStream(tempInputFile, FileMode.Create))
            {
                fileStream.Position = 0;
                await fileStream.CopyToAsync(fileStreamCopy);
            }

            // LibreOffice 경로 가져오기
            var libreOfficePath = GetLibreOfficePath();
            if (string.IsNullOrEmpty(libreOfficePath) || !File.Exists(libreOfficePath))
            {
                _logger.LogWarning("LibreOffice not found. Please install LibreOffice and configure the path in appsettings.json");
                return null;
            }

            // PDF 출력 경로
            var tempOutputFile = Path.Combine(tempDir, "output.pdf");

            // LibreOffice 명령 실행 (headless mode)
            var processInfo = new ProcessStartInfo
            {
                FileName = libreOfficePath,
                Arguments = $"--headless --convert-to pdf --outdir \"{tempDir}\" \"{tempInputFile}\"",
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = tempDir
            };

            using (var process = Process.Start(processInfo))
            {
                if (process == null)
                {
                    _logger.LogError("Failed to start LibreOffice process");
                    return null;
                }

                await process.WaitForExitAsync();
                
                var output = await process.StandardOutput.ReadToEndAsync();
                var error = await process.StandardError.ReadToEndAsync();

                if (process.ExitCode != 0)
                {
                    _logger.LogError("LibreOffice conversion failed. Exit code: {ExitCode}, Error: {Error}", process.ExitCode, error);
                    return null;
                }

                _logger.LogInformation("LibreOffice conversion output: {Output}", output);
            }

            // 변환된 PDF 파일 확인
            var expectedPdfFile = Path.Combine(tempDir, $"input.pdf");
            if (!File.Exists(expectedPdfFile))
            {
                // 파일명이 다를 수 있으므로 PDF 파일 찾기
                var pdfFiles = Directory.GetFiles(tempDir, "*.pdf");
                if (pdfFiles.Length == 0)
                {
                    _logger.LogError("PDF file not found after conversion");
                    return null;
                }
                expectedPdfFile = pdfFiles[0];
            }

            // PDF 파일을 메모리 스트림으로 읽기
            var pdfBytes = await File.ReadAllBytesAsync(expectedPdfFile);
            var pdfStream = new MemoryStream(pdfBytes);

            return pdfStream;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error converting Office file to PDF");
            return null;
        }
        finally
        {
            // 임시 디렉토리 정리 (비동기적으로 처리)
            try
            {
                await Task.Run(() =>
                {
                    try
                    {
                        if (Directory.Exists(tempDir))
                        {
                            Directory.Delete(tempDir, true);
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogWarning(ex, "Failed to delete temp directory: {TempDir}", tempDir);
                    }
                });
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Error cleaning up temp directory: {TempDir}", tempDir);
            }
        }
    }

    private string? GetLibreOfficePath()
    {
        // 설정에서 경로 가져오기
        var configuredPath = _configuration["FileUploadSettings:LibreOfficePath"];
        if (!string.IsNullOrEmpty(configuredPath) && File.Exists(configuredPath))
        {
            return configuredPath;
        }

        // 기본 경로 시도 (Windows)
        var windowsPaths = new[]
        {
            @"C:\Program Files\LibreOffice\program\soffice.exe",
            @"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            @"C:\Program Files\LibreOffice 7\program\soffice.exe"
        };

        foreach (var path in windowsPaths)
        {
            if (File.Exists(path))
            {
                return path;
            }
        }

        // Linux/Mac 기본 경로
        var unixPaths = new[]
        {
            "/usr/bin/libreoffice",
            "/usr/local/bin/libreoffice",
            "/opt/libreoffice/program/soffice"
        };

        foreach (var path in unixPaths)
        {
            if (File.Exists(path))
            {
                return path;
            }
        }

        return null;
    }
}
