let currentStoryIndex = 0;
let currentStories = [];
let currentStoryId = null;

function loadStories() {
    fetch('/social/story/list/')
        .then(response => response.json())
        .then(data => {
            const container = document.getElementById('stories-list');
            if (!container) {
                console.log("container پیدا نشد");
                return;
            }
            container.innerHTML = '';
            
            console.log("داده دریافتی:", data);
            
            Object.values(data).forEach(userData => {
                const user = userData.user;
                if (user.username === currentUsername) {
                    return;
                }
                const hasStory = userData.stories && userData.stories.length > 0;
                
                const storyDiv = document.createElement('div');
                storyDiv.className = 'story-item text-center';
                storyDiv.style.minWidth = '80px';
                storyDiv.style.cursor = 'pointer';
                storyDiv.style.display = 'inline-block';
                storyDiv.onclick = () => showStoryCarousel(userData.stories, user.username);
                
                const ringClass = hasStory ? 'story-ring' : 'story-ring no-story';
                
                storyDiv.innerHTML = `
                    <div class="${ringClass}">
                        <img src="${user.profile_picture || '/media/profiles/default.png'}" style="width: 70px; height: 70px; object-fit: cover;">
                    </div>
                    <small class="text-muted d-block mt-1">${user.username}</small>
                `;
                container.appendChild(storyDiv);
            });
            
            console.log("تعداد استوری‌های نمایش داده شده:", container.children.length);
        })
        .catch(error => console.log('Error loading stories:', error));
}

function showStoryCarousel(stories, username) {
    currentStories = stories;
    currentStoryIndex = 0;
    if (stories.length > 0) {
        currentStoryId = stories[0].id;
    }
    updateCarousel(username);
    const modal = document.getElementById('storyModal');
    if (modal) modal.style.display = 'block';
    
    // نمایش دکمه حذف فقط برای استوری خود کاربر
    const deleteBtn = document.getElementById('deleteStoryBtn');
    if (deleteBtn) {
        const myStoryDiv = document.getElementById('my-story');
        const isMyStory = (username === (myStoryDiv?.querySelector('small')?.innerText === 'تو' ? currentUsername : username));
        deleteBtn.style.display = isMyStory ? 'block' : 'none';
    }
}

function updateCarousel(username) {
    const container = document.getElementById('storyCarouselInner');
    if (!container) return;
    
    const story = currentStories[currentStoryIndex];
    if (!story) {
        container.innerHTML = '<div>استوری وجود ندارد</div>';
        return;
    }
    
    // به‌روزرسانی currentStoryId
    currentStoryId = story.id;
    
    let imageHtml = story.image ? `<img src="${story.image}" style="max-width: 100%; max-height: 400px; border-radius: 12px;">` : '';
    let textHtml = story.text ? `<p style="margin-top: 16px;">${story.text}</p>` : '';
    
    container.innerHTML = `
        <div>
            <h6>${username}</h6>
            ${imageHtml}
            ${textHtml}
            <small style="color: gray; display: block; margin-top: 16px;">${new Date(story.created_at).toLocaleString('fa-IR')}</small>
        </div>
    `;
}

function closeStoryModal() {
    const modal = document.getElementById('storyModal');
    if (modal) modal.style.display = 'none';
}

function prevStory() {
    if (currentStoryIndex > 0) {
        currentStoryIndex--;
        updateCarousel();
    } else {
        closeStoryModal();
    }
}

function nextStory() {
    if (currentStoryIndex < currentStories.length - 1) {
        currentStoryIndex++;
        updateCarousel();
    } else {
        closeStoryModal();
    }
}

function deleteCurrentStory() {
    if (!currentStoryId) return;
    
    if (confirm('آیا از حذف این استوری مطمئن هستید؟')) {
        fetch(`/social/story/delete/${currentStoryId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // حذف از آرایه استوری‌ها
                currentStories.splice(currentStoryIndex, 1);
                
                if (currentStories.length === 0) {
                    closeStoryModal();
                    location.reload(); // رفرش صفحه برای به‌روزرسانی لیست استوری‌ها
                } else {
                    if (currentStoryIndex >= currentStories.length) {
                        currentStoryIndex = currentStories.length - 1;
                    }
                    updateCarousel();
                }
            } else {
                alert('خطا در حذف استوری');
            }
        })
        .catch(error => {
            console.log('Error:', error);
            alert('خطا در حذف استوری');
        });
    }
}

function checkMyStoryAndUpdateRing() {
    fetch('/social/my-stories/')
        .then(response => response.json())
        .then(data => {
            const myStoryRing = document.getElementById('myStoryRing');
            if (!myStoryRing) return;
            
            if (data.stories && data.stories.length > 0) {
                // استوری دارد → حلقه رنگی
                myStoryRing.classList.add("has-story");
                myStoryRing.classList.remove("no-story");
                // با کلیک، استوری‌های خودش را نشان بده
                const myStoryDiv = document.getElementById('my-story');
                if (myStoryDiv) {
                    myStoryDiv.onclick = () => {
                        showStoryCarousel(data.stories, data.username);
                    };
                }
            } else {
                // استوری ندارد → حلقه خاکستری
                myStoryRing.style.background = "#6c757d";
                myStoryRing.style.padding = "2px";
                // با کلیک، آپلود استوری باز شود
                const myStoryDiv = document.getElementById('my-story');
                if (myStoryDiv) {
                    myStoryDiv.onclick = () => {
                        document.getElementById('storyFileInput').click();
                    };
                }
            }
        })
        .catch(error => console.log('Error checking my stories:', error));
}

// تابع کمکی برای دریافت CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// بارگذاری اولیه
document.addEventListener('DOMContentLoaded', function() {
    loadStories();
    checkMyStoryAndUpdateRing();
    
    // بستن مودال با کلیک روی بیرون
    window.onclick = function(event) {
        if (event.target.classList && event.target.classList.contains('modal')) {
            event.target.style.display = 'none';
        }
    }
});