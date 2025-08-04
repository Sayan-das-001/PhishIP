function playSound(file) {
    const audio = new Audio(file);
    audio.play();
}

// Play click sound for buttons
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => playSound('/static/sounds/click.mp3'));
    });
});
