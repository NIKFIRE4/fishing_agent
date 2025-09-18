namespace TgParse.Models
{
    public class TgMessages
    {
        public int Id { get; set; }
        public int MessageId { get; set; }
        public string? MessageText { get; set; }
        public string? СhannelUrl { get; set; }
        public int? PlaceId { get; set; }

        public FishingPlaces? Place { get; set; }
        public List<TgPhotos>? Photos { get; set; } = new List<TgPhotos>();
    }
}
