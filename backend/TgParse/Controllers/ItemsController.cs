using Microsoft.AspNetCore.Mvc;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using DBShared.Models;

namespace TgParse.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ItemsController : ControllerBase
    {
        private static List<Item> _items = new() { new Item { Id = 1, Name = "Item1" } };

        [HttpGet]
        public IActionResult Get() => Ok(_items);

        [HttpGet("{id}")]
        public IActionResult Get(int id)
        {
            var item = _items.FirstOrDefault(x => x.Id == id);
            return item == null ? NotFound() : Ok(item);
        }

        [HttpPost]
        public IActionResult Post([FromBody] Item item)
        {
            item.Id = _items.Count + 1;
            _items.Add(item);
            return CreatedAtAction(nameof(Get), new { id = item.Id }, item);
        }

        [HttpPut("{id}")]
        public IActionResult Put(int id, [FromBody] Item item)
        {
            var existing = _items.FirstOrDefault(x => x.Id == id);
            if (existing == null) return NotFound();
            existing.Name = item.Name;
            return NoContent();
        }

        [HttpDelete("{id}")]
        public IActionResult Delete(int id)
        {
            var item = _items.FirstOrDefault(x => x.Id == id);
            if (item == null) return NotFound();
            _items.Remove(item);
            return NoContent();
        }
    }
}
