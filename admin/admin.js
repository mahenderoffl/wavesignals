const ADMIN_KEY = "wavesignals@2025"; // change later

const loginScreen = document.getElementById("login-screen");
const adminPanel = document.getElementById("admin-panel");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const error = document.getElementById("login-error");

loginBtn.onclick = () => {
  const key = document.getElementById("admin-key").value;
  if (key === ADMIN_KEY) {
    loginScreen.classList.add("hidden");
    adminPanel.classList.remove("hidden");
    loadPosts();
  } else {
    error.classList.remove("hidden");
  }
};

logoutBtn.onclick = () => location.reload();

async function loadPosts() {
  const res = await fetch("../content/posts.json");
  const posts = await res.json();
  const list = document.getElementById("posts-list");
  list.innerHTML = "";

  posts.forEach(p => {
    const li = document.createElement("li");
    li.textContent = `${p.title} — ${p.status}`;
    list.appendChild(li);
  });
}

document.getElementById("save-post").onclick = async () => {
  const title = document.getElementById("title").value;
  const slugInput = document.getElementById("slug").value;
  const slug = slugInput || title.toLowerCase().replace(/\s+/g, "-");
  const excerpt = document.getElementById("excerpt").value;
  const content = document.getElementById("content").value;
  const publish = document.getElementById("publish").checked;

  const post = {
    id: "ws-" + Date.now(),
    title,
    slug,
    excerpt,
    content,
    publishedAt: new Date().toISOString(),
    status: publish ? "published" : "draft"
  };

  alert(
    "Post object created.\n\n" +
    "In Phase 2.2 we wire saving to posts.json automatically.\n\n" +
    JSON.stringify(post, null, 2)
  );
};
