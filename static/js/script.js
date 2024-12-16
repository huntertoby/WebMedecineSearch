// static/js/script.js

// 定義暫存對象，使用 Map 來存儲查詢結果
const cache = new Map();

let currentPage = 1;
let currentQueryValue = "";
let totalPage = 1;

window.onload = function() {
    clearError();
};

document.getElementById("searchBtn").addEventListener("click", function() {
    currentQueryValue = document.getElementById("searchValue").value.trim();
    const hasImage = document.getElementById("hasImage").checked;
    if (!currentQueryValue) {
        showError("請輸入查詢值");
        return;
    }
    currentPage = 1;
    fetchResults(hasImage);
});

document.getElementById("prevPageBtn").addEventListener("click", function() {
    if (currentPage > 1) {
        currentPage--;
        const hasImage = document.getElementById("hasImage").checked;
        fetchResults(hasImage);
    }
});

document.getElementById("nextPageBtn").addEventListener("click", function() {
    if (currentPage < totalPage) {
        currentPage++;
        const hasImage = document.getElementById("hasImage").checked;
        fetchResults(hasImage);
    }
});

document.getElementById("pageSelect").addEventListener("change", function() {
    const selectedPage = parseInt(this.value, 10);
    if (!isNaN(selectedPage) && selectedPage >= 1 && selectedPage <= totalPage) {
        currentPage = selectedPage;
        const hasImage = document.getElementById("hasImage").checked;
        fetchResults(hasImage);
    }
});

document.getElementById("hasImage").addEventListener("change", function() {
    // 當勾選框狀態改變時，重新搜尋
    currentPage = 1;
    const hasImage = this.checked;
    if (currentQueryValue) {
        fetchResults(hasImage);
    }
});

// 增加回車鍵觸發搜尋功能
document.getElementById("searchValue").addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        document.getElementById("searchBtn").click();
    }
});

function generateCacheKey(query, page, hasImage) {
    return `${query}|${page}|${hasImage}`;
}

function fetchResults(hasImage) {
    clearError();
    showLoading(true);
    const cacheKey = generateCacheKey(currentQueryValue, currentPage, hasImage);

    // 檢查暫存中是否有該查詢結果
    if (cache.has(cacheKey)) {
        console.log(`從暫存中獲取結果：${cacheKey}`);
        showResults(cache.get(cacheKey));
        showLoading(false);
        return;
    }

    // 如果沒有，則發送請求
    fetch(`/search?value=${encodeURIComponent(currentQueryValue)}&page=${currentPage}&has_image=${hasImage}`)
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {throw data});
            }
            return response.json();
        })
        .then(data => {
            // 將結果存入暫存
            cache.set(cacheKey, data);
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
        })
        .finally(() => {
            showLoading(false);
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
        const introductions = item["藥品介紹"] || [];

        // 只保留有至少一個連結的介紹
        const validIntroductions = introductions.filter(intro => intro["仿單圖檔連結"] || intro["外盒圖檔連結"]);

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

        if (appearance.length > 0) {
            const appearanceSection = document.createElement("div");
            appearanceSection.className = "appearance";
            appearanceSection.innerHTML = `<h3>外觀</h3>`;
            const ul = document.createElement("ul");
            appearance.forEach(app => {
                const li = document.createElement("li");
                li.textContent = `形狀: ${app["形狀"] || "無"} 顏色: ${app["顏色"] || "無"}`;
                ul.appendChild(li);
            });
            appearanceSection.appendChild(ul);
            resultItem.appendChild(appearanceSection);
        }

        // 顯示外觀圖片
        const imageUrls = appearance.map(app => app["外觀圖檔連結"]).filter(url => url);
        if (imageUrls.length > 0) {
            const imageContainer = document.createElement("div");
            imageContainer.className = "image-container";
            imageUrls.forEach(url => {
                const img = document.createElement("img");
                img.src = url;
                img.alt = "藥品外觀圖片";
                imageContainer.appendChild(img);
            });
            resultItem.appendChild(imageContainer);
        }

        // 顯示藥品介紹（僅當有有效連結時）
        if (validIntroductions.length > 0) {
            const introductionSection = document.createElement("div");
            introductionSection.className = "introduction";
            introductionSection.innerHTML = `<h3>藥品介紹</h3>`;
            const ul = document.createElement("ul");

            validIntroductions.forEach(intro => {
                const li = document.createElement("li");
                // 檢查是否有仿單圖檔連結和外盒圖檔連結
                const instructionLink = intro["仿單圖檔連結"] ? `<a href="${intro["仿單圖檔連結"]}" target="_blank">仿單下載</a>` : "";
                const boxImageLink = intro["外盒圖檔連結"] ? `<a href="${intro["外盒圖檔連結"]}" target="_blank">外盒圖檔</a>` : "";
                li.innerHTML = `${instructionLink} ${boxImageLink}`;
                ul.appendChild(li);
            });

            introductionSection.appendChild(ul);
            resultItem.appendChild(introductionSection);
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

function showLoading(isLoading) {
    const loadingIndicator = document.getElementById("loadingIndicator");
    if (isLoading) {
        loadingIndicator.style.display = "block";
        document.getElementById("resultsWrapper").style.display = "none";
    } else {
        loadingIndicator.style.display = "none";
    }
}
