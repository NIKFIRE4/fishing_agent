namespace TgParse.Models
{
    public class FishingPlaces
    {
        public int Id { get; set; }
        public string? Name{ get; set; }
        public decimal? Latitude { get; set; }
        public decimal? Longitude { get; set; }
        public string? CaughtFishes { get; set; }
        public string? WaterPlace { get; set; }
        public string? PlaceDescription { get; set; }

        public List<FishingPlaceWater> FishingPlaceWaters { get; set; } = new List<FishingPlaceWater>();
        public List<FishingPlaceFish> FishingPlaceFishes { get; set; } = new List<FishingPlaceFish>();
        public List<TgMessages>? Messages { get; set; } = new List<TgMessages>();
    }
}
