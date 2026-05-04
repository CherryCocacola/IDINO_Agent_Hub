using AIAgentManagement.DTOs;

namespace AIAgentManagement.Services;

public interface IPptxTemplateParser
{
    Task<TemplateStructureDto> ParseTemplateAsync(Stream pptxStream, CancellationToken cancellationToken = default);
}
