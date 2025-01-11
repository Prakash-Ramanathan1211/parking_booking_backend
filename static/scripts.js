document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('addMarkerForm');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(form);

        try {
            const response = await fetch('/add_marker', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (result.success) {
                alert('Marker added successfully!');
            } else {
                alert('Error adding marker: ' + result.error);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to add marker.');
        }
    });
});
