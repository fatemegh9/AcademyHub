// توابع استوری
function loadStories() {
    fetch('/social/story/list/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('stories-list');
            if (!container) return;
            
            container.innerHTML = '';
            
            Object.values(data).forEach(userData => {
                const user = userData.user;
                const storyDiv = document.createElement('div');
                storyDiv.className = 'story-item text-center';
                storyDiv.style.minWidth = '80px';
                storyDiv.onclick = () => showStoryCarousel(userData.stories, user.username);
                storyDiv.innerHTML = `
                    <div class="story-ring">
                        <img src="${user.profile_picture || 'https://randomuser.me/api/portraits/lego/1.jpg'}" 
                             class="rounded-circle" style="width: 70px; height: 70px; object-fit: cover;">
                    </div>
                    <small class="text-muted d-block mt-1">${user.username}</small>
                `;
                container.appendChild(storyDiv);
            });
        });
}

function showStoryCarousel(stories, username) {
    const carouselInner = document.getElementById('storyCarouselInner');
    if (!carouselInner) return;
    
    carouselInner.innerHTML = '';
    
    stories.forEach((story, index) => {
        const div = document.createElement('div');
        div.className = `carousel-item ${index === 0 ? 'active' : ''}`;
        div.innerHTML = `
            <div class="text-center p-4">
                <h6>${username}</h6>
                ${story.image ? `<img src="${story.image}" class="img-fluid rounded" style="max-height: 400px;">` : ''}
                ${story.text ? `<p class="mt-3">${story.text}</p>` : ''}
                <small class="text-muted">${new Date(story.created_at).toLocaleString('fa-IR')}</small>
            </div>
        `;
        carouselInner.appendChild(div);
    });
    
    const modal = new bootstrap.Modal(document.getElementById('storyViewModal'));
    modal.show();
}

// بارگذاری خودکار استوری‌ها
document.addEventListener('DOMContentLoaded', function() {
    loadStories();
});