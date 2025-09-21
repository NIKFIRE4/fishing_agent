namespace TgParse.Models
{
    public class WaterType
    {
        public int Id { get; set; }
        public string? Name { get; set; }
        public List<FishingPlaceWater> FishingPlaceWaters { get; set; } = new List<FishingPlaceWater>();
    }
}
