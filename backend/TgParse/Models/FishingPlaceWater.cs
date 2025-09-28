namespace TgParse.Models
{
    public class FishingPlaceWater
    {
        public int FishingPlaceId { get; set; }
        public FishingPlaces? FishingPlaces { get; set; }

        public int WaterTypeId { get; set; }
        public WaterType? WaterType { get; set; }
    }
}
