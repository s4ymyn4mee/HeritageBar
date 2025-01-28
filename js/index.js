const scroll = document.querySelector('.scroll-top');
window.addEventListener('scroll', () => {
    if (this.scrollY >= 450)
        scroll.style.opacity = '1'
    else
        scroll.style.opacity = '0'
})

const more = document.querySelector('.more');
const showMoreElement = document.querySelector('.show-more');
let showMoreIsHidden = false;
showMoreElement.addEventListener('click', () => {
    if (!showMoreIsHidden) {
        more.style.display = 'block';
        showMoreElement.textContent = 'Свернуть';
        showMoreIsHidden = true;
    }
    else {
        more.style.display = 'none';
        showMoreElement.textContent = 'Читать больше';
        showMoreIsHidden = false;
    }
});
