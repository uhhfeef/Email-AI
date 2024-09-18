// Function to add thumbs up emoji
function addThumbsUpEmoji() {
    observer.disconnect();
    const emailRows = document.querySelectorAll('.zA'); 
    emailRows.forEach(row => {
        if (!row.querySelector('.thumbs-up-emoji')) { 
            const emojiSpan = document.createElement('span');
            emojiSpan.textContent = '👍'; // Thumbs up emoji
            emojiSpan.className = 'thumbs-up-emoji';

            const dateElement = row.querySelector('.xW.xY');
            dateElement.insertBefore(emojiSpan, dateElement.firstChild);
            console.log('hello');
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });    
}

// Observe changes in the DOM to dynamically add emojis as new emails load
const observer = new MutationObserver(addThumbsUpEmoji);
observer.observe(document.body, { childList: true, subtree: true });