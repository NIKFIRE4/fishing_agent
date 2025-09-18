
using TgParse.Models;

namespace TgParse
{
    public class FishingPlaces
    {
        public int PlaceId { get; set; }
        public string? PlaceName { get; set; }
        public string? Coordinates { get; set; }
        public string? CaughtFishes { get; set; }
        public string? WaterPlace { get; set; }
        public string? PlaceDescription { get; set; }
        public List<TgMessages>? IdTgMessage { get; set; } = new List<TgMessages>();
    }
}
