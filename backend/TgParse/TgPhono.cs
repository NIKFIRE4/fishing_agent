namespace TgParse.Models
{
    public class TgPhotos
    {
        public int Id { get; set; }
        public string? PhotoUrl { get; set; }
        public int MessageId { get; set; }

        public TgMessages? Message { get; set; }
    }
}
