let currentPage = 1;
let currentQueryValue = "";
let totalPage = 1;

document.getElementById("searchBtn").addEventListener("click", function() {
    currentQueryValue = document.getElementById("searchValue").value.trim();
    if (!currentQueryValue) {
        showError("請輸入查詢值");
        return;
    }
    currentPage = 1;
    fetchResults();
});

document.getElementById("prevPageBtn").addEventListener("click", function() {
    if (currentPage > 1) {
        currentPage--;
        fetchResults();
    }
});

document.getElementById("nextPageBtn").addEventListener("click", function() {
    if (currentPage < totalPage) {
        currentPage++;
        fetchResults();
    }
});

document.getElementById("pageSelect").addEventListener("change", function() {
    const selectedPage = parseInt(this.value, 10);
    if (!isNaN(selectedPage) && selectedPage >= 1 && selectedPage <= totalPage) {
        currentPage = selectedPage;
        fetchResults();
    }
});

function fetchResults() {
    clearError();
    fetch(`/search?value=${encodeURIComponent(currentQueryValue)}&page=${currentPage}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {throw data});
            }
            return response.json();
        })
        .then(data => {
            showResults(data);
        })
        .catch(err => {
            if (err && err.message) {
                showError(err.message);
            } else if (err && err.error) {
                showError(err.error);
            } else {
                showError("發生錯誤");
            }
        });
}

function showResults(data) {
    const resultContainer = document.getElementById("resultContainer");
    resultContainer.innerHTML = "";
    document.getElementById("resultsWrapper").style.display = "block";

    totalPage = data.pages;

    data.results.forEach(item => {
        const detailed = item["詳細資料"] || {};
        const components = item["成份內容"] || [];
        const appearance = item["外觀"] || [];

        const resultItem = document.createElement("div");
        resultItem.className = "result-item";

        const drugInfoDiv = document.createElement("div");
        drugInfoDiv.className = "drug-info";

        drugInfoDiv.innerHTML = `
            <p><strong>許可證字號：</strong>${detailed["許可證字號"] || ""}</p>
            <p><strong>中文品名：</strong>${detailed["中文品名"] || ""}</p>
            <p><strong>英文品名：</strong>${detailed["英文品名"] || ""}</p>
            <p><strong>適應症：</strong>${detailed["適應症"] || ""}</p>
            <p><strong>用法用量：</strong>${detailed["用法用量"] || ""}</p>
            <p><strong>製造廠國別：</strong>${detailed["製造廠國別"] || ""}</p>
            <p><strong>發證日期：</strong>${detailed["發證日期"] || ""}</p>
            <p><strong>有效日期：</strong>${detailed["有效日期"] || ""}</p>
        `;
        resultItem.appendChild(drugInfoDiv);

        if (components.length > 0) {
            const componentsSection = document.createElement("div");
            componentsSection.className = "components";
            componentsSection.innerHTML = `<h3>成份內容</h3>`;
            const ul = document.createElement("ul");
            components.forEach(comp => {
                const li = document.createElement("li");
                li.textContent = `${comp["成分名稱"] || ""} - ${comp["含量"] || ""} ${comp["含量單位"] || ""}`;
                ul.appendChild(li);
            });
            componentsSection.appendChild(ul);
            resultItem.appendChild(componentsSection);
        }

        let imageUrl = "";
        if (appearance.length > 0) {
            const appearanceSection = document.createElement("div");
            appearanceSection.className = "appearance";
            appearanceSection.innerHTML = `<h3>外觀</h3>`;
            const ul = document.createElement("ul");
            appearance.forEach(app => {
                const li = document.createElement("li");
                li.textContent = `形狀:${app["形狀"] || "無"} 顏色:${app["顏色"] || "無"}`;
                ul.appendChild(li);
                if (app["外觀圖檔連結"]) {
                    imageUrl = app["外觀圖檔連結"];
                }
            });
            appearanceSection.appendChild(ul);
            resultItem.appendChild(appearanceSection);
        }

        if (imageUrl) {
            const imageContainer = document.createElement("div");
            imageContainer.className = "image-container";
            imageContainer.innerHTML = `<h3>外觀圖片</h3><img src="${imageUrl}" alt="drug image"/>`;
            resultItem.appendChild(imageContainer);
        }

        resultContainer.appendChild(resultItem);
    });

    const paginationContainer = document.getElementById("paginationContainer");
    paginationContainer.style.display = totalPage > 1 ? "flex" : "none";

    document.getElementById("prevPageBtn").disabled = currentPage <= 1;
    document.getElementById("nextPageBtn").disabled = currentPage >= totalPage;

    const pageSelect = document.getElementById("pageSelect");
    pageSelect.innerHTML = "";
    for (let i = 1; i <= totalPage; i++) {
        const option = document.createElement("option");
        option.value = i;
        option.textContent = i;
        if (i === data.page) {
            option.selected = true;
        }
        pageSelect.appendChild(option);
    }
}

function showError(message) {
    const errorDiv = document.getElementById("errorContainer");
    errorDiv.innerHTML = message;
    errorDiv.style.display = "block";
    document.getElementById("resultsWrapper").style.display = "none";
}

function clearError() {
    const errorDiv = document.getElementById("errorContainer");
    errorDiv.innerHTML = "";
    errorDiv.style.display = "none";
}
