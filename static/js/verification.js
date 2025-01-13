document.addEventListener('DOMContentLoaded', () => {
    const toggleButtons = document.querySelectorAll('.level-toggle');
    const verificationLevels = document.querySelectorAll('.verification-level');

    toggleButtons.forEach(button => {
        button.addEventListener('click', () => {
            const level = button.dataset.level;
            
            // Update button states
            toggleButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show/hide appropriate content
            verificationLevels.forEach(section => {
                if (section.classList.contains(`${level}-verification`)) {
                    section.style.display = 'block';
                    // Trigger re-flow for animation
                    setTimeout(() => section.style.opacity = '1', 10);
                } else {
                    section.style.opacity = '0';
                    setTimeout(() => section.style.display = 'none', 300);
                }
            });
        });
    });
});
