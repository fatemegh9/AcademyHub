// توابع تایم‌لاین (کامنت، لایک، ویرایش)
function toggleCommentForm(postId) {
    const form = document.getElementById('comment-form-' + postId);
    if (form) {
        form.style.display = form.style.display === 'none' ? 'block' : 'none';
    }
}

function showEditForm(postId) {
    const form = document.getElementById('edit-form-' + postId);
    if (form) form.style.display = 'block';
}

function hideEditForm(postId) {
    const form = document.getElementById('edit-form-' + postId);
    if (form) form.style.display = 'none';
}

function showEditNoteForm(noteId) {
    const form = document.getElementById('edit-note-form-' + noteId);
    if (form) form.style.display = 'block';
}

function hideEditNoteForm(noteId) {
    const form = document.getElementById('edit-note-form-' + noteId);
    if (form) form.style.display = 'none';
}

function deleteComment(commentId, el) {
    fetch(`/social/comment/delete/${commentId}/`, {
        method: "GET",
        headers: {
            "X-Requested-With": "XMLHttpRequest"
        }
    })
    .then(res => {
        if (res.ok) {
            el.closest(".comment-item").remove();
        } else {
            console.log("delete failed");
        }
    })
    .catch(err => console.log(err));
}

function toggleMenu(btn){
    const menu = btn.nextElementSibling;
    menu.style.display = (menu.style.display === "flex") ? "none" : "flex";
}