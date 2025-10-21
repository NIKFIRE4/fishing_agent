using DBShared;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using System.ComponentModel.DataAnnotations;

namespace AgentBackend.Controllers
{    
        
    [ApiController]
    [Route("api/[controller]")]
    public class BotApi : ControllerBase
    {
        private readonly ApplicationContext _context;

        public BotApi(ApplicationContext context)
        {
            _context = context;
        }

        public class PlaceTypeRequest
        {
            [Required(ErrorMessage = "PlaceType is required")]
            public string PlaceType { get; set; } = string.Empty;
        }

        [HttpPost("by-type")]
        public async Task<IActionResult> GetPlacesByType([FromBody] PlaceTypeRequest request)
        {
            try
            {
                // Проверка валидности входных данных
                if (!ModelState.IsValid)
                {
                    return BadRequest(ModelState);
                }

                // Фильтрация мест по типу туризма
                var places = await _context.Places
                    .Where(p => p.PlaceType == request.PlaceType)
                    .Select(p => new
                    {
                        p.IdPlace,
                        p.PlaceName,
                        p.Latitude,
                        p.Longitude,
                        p.PlaceDescription,
                        p.PlaceType
                    })
                    .ToListAsync();

                // Проверка, найдены ли записи
                if (places == null || places.Count == 0)
                {
                    return NotFound(new { Message = $"No places found for type '{request.PlaceType}'" });
                }

                // Возвращаем JSON с результатами
                return Ok(places);
            }
            catch (Exception ex)
            {
                // Логирование ошибки
                Console.WriteLine($"Error in GetPlacesByType: {ex.Message}");
                return StatusCode(500, new { Message = "An error occurred while fetching places" });
            }
        }


        
    }
}
