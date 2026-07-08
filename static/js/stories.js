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
                storyDiv.onclick = () => showStoryCarousel(userData.stories, user.username, user.profile_picture);
                
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

let currentStoryUsername = null;
let currentStoryAvatar = null;

function showStoryCarousel(stories, username, avatarUrl) {
    currentStories = stories;
    currentStoryIndex = 0;
    currentStoryUsername = username;
    currentStoryAvatar = avatarUrl;
    if (stories.length > 0) {
        currentStoryId = stories[0].id;
    }

    updateHeader();
    updateCarousel();

    const modal = document.getElementById('storyModal');
    if (modal) modal.style.display = 'block';

    const deleteBtn = document.getElementById('deleteStoryBtn');
    if (deleteBtn) {
        const myStoryDiv = document.getElementById('my-story');
        const isMyStory = (username === (myStoryDiv?.querySelector('small')?.innerText === 'تو' ? currentUsername : username));
        deleteBtn.style.display = isMyStory ? 'block' : 'none';
    }
}

function updateHeader() {
    const nameEl = document.getElementById('stmUsername');
    const avatarEl = document.getElementById('stmAvatar');
    if (nameEl) nameEl.textContent = currentStoryUsername || '';
    if (avatarEl) {
        avatarEl.innerHTML = currentStoryAvatar
            ? `<img src="${currentStoryAvatar}" alt="${currentStoryUsername}">`
            : (currentStoryUsername ? currentStoryUsername.charAt(0).toUpperCase() : '');
    }
}

function updateCarousel() {
    const container = document.getElementById('storyCarouselInner');
    if (!container) return;

    const story = currentStories[currentStoryIndex];
    if (!story) {
        container.innerHTML = '<div class="stm-text">استوری وجود ندارد</div>';
        return;
    }

    currentStoryId = story.id;

    let imageHtml = story.image ? `<img src="${story.image}" alt="">` : '';
    let textHtml = story.text ? `<p class="stm-text">${story.text}</p>` : '';

    container.innerHTML = `
        ${imageHtml}
        ${textHtml}
        <small style="color:#7a8fbb; display:block; margin-top:8px; font-size:12px;">${new Date(story.created_at).toLocaleString('fa-IR')}</small>
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

    const fakeForm = {
        submit: function() {
            closeConfirmModal();
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
                    currentStories.splice(currentStoryIndex, 1);

                    if (currentStories.length === 0) {
                        closeStoryModal();
                        location.reload();
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
    };

    openConfirmModal(
        fakeForm,
        'حذف استوری',
        'آیا از حذف این استوری مطمئن هستید؟ این عملیات قابل بازگشت نیست.'
    );
}

function uploadNewStory(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('image', file);

    fetch('/social/story/create/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            return fetch('/social/my-stories/')
                .then(res => res.json())
                .then(myData => {
                    currentStories = myData.stories;
                    currentStoryIndex = 0;
                    currentStoryUsername = myData.username;
                    currentStoryAvatar = myData.profile_picture;
                    updateHeader();
                    updateCarousel();

                    const modal = document.getElementById('storyModal');
                    if (modal) modal.style.display = 'block';

                    const deleteBtn = document.getElementById('deleteStoryBtn');
                    if (deleteBtn) deleteBtn.style.display = 'block';

                    checkMyStoryAndUpdateRing();
                });
        } else {
            alert(data.error || 'خطا در آپلود استوری');
        }
    })
    .catch(error => {
        console.log('Error uploading story:', error);
        alert('خطا در آپلود استوری');
    })
    .finally(() => {
        event.target.value = '';
    });
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
                        showStoryCarousel(data.stories, data.username, data.profile_picture);
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