function sendForm(){
  const toast = document.getElementById('toast');
  toast.style.display = 'block';
  setTimeout(()=>{ toast.style.display='none'; }, 5000);
}
