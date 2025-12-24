const ADMIN_KEY = "wavesignals@2025"; // Simple auth for now

const loginScreen = document.getElementById("login-screen");
const adminPanel = document.getElementById("admin-panel");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const error = document.getElementById("login-error");

// Mock Auth Check
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

// Load Posts from Server API
async function loadPosts() {
  const list = document.getElementById("posts-list");
  list.innerHTML = "<li>Loading...</li>";

  try {
    const res = await fetch("http://localhost:3000/api/posts");
    if (!res.ok) throw new Error("Failed to load");
    const data = await res.json();
    const posts = data.posts || [];

    list.innerHTML = "";
    posts.forEach(p => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${p.title}</strong> <span class="badge ${p.status}">${p.status}</span>`;
      li.onclick = () => loadIntoEditor(p);
      list.appendChild(li);
    });
  } catch (e) {
    list.innerHTML = "<li>Error loading posts. Is server.js running?</li>";
    console.error(e);
  }
}

function loadIntoEditor(post) {
  document.getElementById("title").value = post.title;
  document.getElementById("slug").value = post.slug;
  document.getElementById("excerpt").value = post.excerpt || "";
  document.getElementById("content").value = post.content || "";
  document.getElementById("publish").checked = (post.status === "published");

  // Store ID for updating
  document.getElementById("save-post").dataset.id = post.id;
  document.getElementById("save-post").dataset.date = post.date; // Keep original date
}

// Save Post to Server API
document.getElementById("save-post").onclick = async function () {
  const btn = this;
  const originalLabel = btn.textContent;
  btn.textContent = "Saving...";

  const title = document.getElementById("title").value;
  const slug = document.getElementById("slug").value || title.toLowerCase().replace(/[^a-z0-9]+/g, "-");
  const excerpt = document.getElementById("excerpt").value;
  const content = document.getElementById("content").value;
  const publish = document.getElementById("publish").checked;

  const id = btn.dataset.id || "ws-" + Date.now();
  const date = btn.dataset.date || new Date().toISOString();

  const post = {
    id,
    title,
    slug,
    excerpt,
    content,
    date,
    published: publish,
    status: publish ? "published" : "draft"
  };

  try {
    const res = await fetch("http://localhost:3000/api/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ post })
    });

    if (res.ok) {
      alert("Post Saved Successfully!");
      loadPosts(); // Refresh list
      // clear editor if new? No, keep it open.
    } else {
      alert("Error saving post.");
    }
  } catch (e) {
    console.error(e);
    alert("Network error. Is server.js running?");
  }

  btn.textContent = originalLabel;
};
