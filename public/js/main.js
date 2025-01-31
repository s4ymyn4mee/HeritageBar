const burger = document.querySelector('.burger');
const navigation = document.querySelector('.navigation');
const header = document.querySelector('.header');

let showedNavigation = false;

burger.addEventListener('click', () => {
    if (!showedNavigation) {
        navigation.style['margin-top'] = "85px";
        showedNavigation = true;
    }
    else {
        navigation.style['margin-top'] = "-160px";
        showedNavigation = false;
    }
});

window.addEventListener('scroll', () => {
    header.style.boxShadow = '0 4px 4px rgba(0, 0, 0, 0.1)';
    // if (this.scrollY >= 160)
    //     header.style.boxShadow = '0 4px 4px rgba(0, 0, 0, 0.1)'
    // else
    //     header.style.boxShadow = '0 0px 0px rgba(0, 0, 0, 0.1)'
});
