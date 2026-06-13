// home.js — mood filters + live wall small animations

document.addEventListener('DOMContentLoaded', function(){

  /* ---------------------------------------
     MOOD CHIPS — front-end visual filtering
  -----------------------------------------*/

  // MOOD chips (genre-based filter)
const chips = document.querySelectorAll('.chip');
const cards = document.querySelectorAll('.media-card');

chips.forEach(chip => {
  chip.addEventListener('click', () => {

    chips.forEach(c => c.classList.remove('active'));
    chip.classList.add('active');

    const mood = chip.dataset.mood;

    cards.forEach(card => {
      const genres = (card.dataset.genre || "").toLowerCase();

      if (mood === "all") {
        card.style.display = "";
      } 
      else if (mood === "thrilling") {
        card.style.display = genres.includes("action") ||
                             genres.includes("thriller") ||
                             genres.includes("crime") ||
                             genres.includes("adventure") ? "" : "none";
      }
      else if (mood === "romantic") {
        card.style.display = genres.includes("romance") ||
                             genres.includes("love") ||
                             genres.includes("drama") ? "" : "none";
      }
      else if (mood === "funny") {
        card.style.display = genres.includes("comedy") ? "" : "none";
      }
      else if (mood === "dark") {
        card.style.display = genres.includes("horror") ||
                             genres.includes("thriller") ||
                             genres.includes("mystery") ? "" : "none";
      }
      else if (mood === "inspirational") {
        card.style.display = genres.includes("biography") ||
                             genres.includes("sports") ||
                             genres.includes("history") ||
                             genres.includes("motivational") ? "" : "none";
      }
    });

  });
});

  /* ---------------------------------------
     LIVE WALL — small fade-in tiles
  -----------------------------------------*/

  const tiles = document.querySelectorAll(".live-tile");
  if (tiles) {
    tiles.forEach((tile, i) => {
      setTimeout(() => tile.classList.add("visible"), i * 80);
    });
  }

});
