using System.ComponentModel.DataAnnotations;

namespace TgParse.Models
{
    public class FishingPlaces
    {
        [Key] 
        public int IdFishingPlace { get; set; }
        public string? PlaceName{ get; set; }
        public decimal? Latitude { get; set; }
        public decimal? Longitude { get; set; }
        public string? PlaceDescription { get; set; }

        public List<FishingPlaceWater> FishingPlaceWaters { get; set; } = new List<FishingPlaceWater>();
        public List<FishingPlaceFish> FishingPlaceFishes { get; set; } = new List<FishingPlaceFish>();
        public List<TgMessages>? Messages { get; set; } = new List<TgMessages>();
    }
}
