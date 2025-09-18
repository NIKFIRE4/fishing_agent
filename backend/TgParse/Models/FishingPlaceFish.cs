namespace TgParse.Models
{
    public class FishingPlaceFish
    {
        public int FishingPlaceId { get; set; }
        public FishingPlaces? FishingPlace { get; set; }

        public int FishTypeId { get; set; }
        public FishType? FishType { get; set; }
    }
}
