using Microsoft.AspNetCore.Mvc;
using TgParse.Services;
using System.Text.Json;
using System.Threading.Tasks;

namespace TgParse.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class TelegramParserController : ControllerBase
    {
        private static bool _isParsingRunning = false;
        private readonly MessageComparor _processorService;
        public TelegramParserController(MessageComparor processorService)
        {
            _processorService = processorService;
        }

        [HttpPost("start")]
        public async Task<IActionResult> StartParsing()
        {
            if (_isParsingRunning)
            {
                return BadRequest("Парсинг уже выполняется. Пожалуйста, дождитесь завершения.");
            }

            try
            {
                _isParsingRunning = true;
                Console.WriteLine("Начало парсинга...");
                await TelegramParser.RunApplication();
                Console.WriteLine("Парсинг завершен.");
                return Ok("Парсинг успешно выполнен.");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Ошибка при выполнении парсинга: {ex.Message}");
                return StatusCode(500, $"Ошибка при выполнении парсинга: {ex.Message}");
            }
            finally
            {
                _isParsingRunning = false;
            }
        }

        [HttpPost("compare")]
        public async Task<IActionResult> ComparePlaces()
        {
            

            try
            {
                Console.WriteLine($"Начало обработки сообщений");
                await _processorService.ProcessUnprocessedMessagesAsync();
                return Ok("Сообщения обработаны.");
                

                // Возвращаем JSON-документ как строку для удобства

            }
            catch (Exception ex)
            {
                Console.WriteLine($"Ошибка при сравнении мест: {ex.Message}");
                return StatusCode(500, $"Ошибка при сравнении мест: {ex.Message}");
            }
        }
    }

    public class CompareRequest
    {
        public string Message { get; set; }
    }
}