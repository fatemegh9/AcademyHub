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