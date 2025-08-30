document.addEventListener("load", main())
function main () {
    image = document.querySelector('.pas_img')
    image2 = document.querySelector('.pas_img2')
    input = document.getElementById('id_password')
    image.addEventListener("click",()=>{
        image2.style.display="block";
        image.style.display="none";
        input.type = 'text'
    });
    image2.addEventListener("click", ()=>{
        image2.style.display="none";
        image.style.display="block";
        input.type = 'password'
    })
}
