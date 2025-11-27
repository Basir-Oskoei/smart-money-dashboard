const statusEl = document.getElementById("status");
const biasSummaryEl = document.getElementById("biasSummary");
const pdFillEl = document.getElementById("pdFill");
const pdLabelEl = document.getElementById("pdLabel");
const detailsEl = document.getElementById("details");
const uploadBtn = document.getElementById("uploadBtn");
const sampleBtn = document.getElementById("sampleBtn");
const fileInput = document.getElementById("csvFile");

let chart;
let candleSeries;
let liquiditySeries;

let fvgTopSeries = [];
let fvgBottomSeries = [];

function setStatus(message) {
    statusEl.textContent = message;
}

function createChart() {
    const container = document.getElementById("chart");
    container.innerHTML = "";

    chart = LightweightCharts.createChart(container, {
        layout: {
            background: { color: "#020617" },
            textColor: "#e5e7eb",
        },
        grid: {
            vertLines: { color: "#0f172a" },
            horzLines: { color: "#0f172a" },
        },
        timeScale: {
            borderColor: "#1f2937",
        },
        rightPriceScale: {
            borderColor: "#1f2937",
        },
    });

    candleSeries = chart.addCandlestickSeries({
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderVisible: false,
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
    });

    liquiditySeries = chart.addLineSeries({
        color: "#eab308",
        lineWidth: 1,
    });
}

function clearFvgSeries() {
    if (!chart) return;
    fvgTopSeries.forEach(s => chart.removeSeries(s));
    fvgBottomSeries.forEach(s => chart.removeSeries(s));
    fvgTopSeries = [];
    fvgBottomSeries = [];
}

function renderFvgs(fvgs) {
    clearFvgSeries();
    if (!chart || !fvgs || !fvgs.length) return;

    const maxFvgs = 8;
    const recentFvgs = fvgs.slice(-maxFvgs);

    recentFvgs.forEach(fvg => {
        const t1 = Math.floor(new Date(fvg.timestamp_a).getTime() / 1000);
        const t2 = Math.floor(new Date(fvg.timestamp_c).getTime() / 1000);

        const topSeries = chart.addLineSeries({
            color: "rgba(56, 189, 248, 0.7)",
            lineWidth: 1,
        });

        const bottomSeries = chart.addLineSeries({
            color: "rgba(56, 189, 248, 0.3)",
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dotted,
        });

        topSeries.setData([
            { time: t1, value: fvg.gap_high },
            { time: t2, value: fvg.gap_high },
        ]);

        bottomSeries.setData([
            { time: t1, value: fvg.gap_low },
            { time: t2, value: fvg.gap_low },
        ]);

        fvgTopSeries.push(topSeries);
        fvgBottomSeries.push(bottomSeries);
    });
}

function renderBias(data) {
    const bias = data.bias;
    const explanation = data.bias_explanation || [];
    const score = data.bias_score || 0;

    let labelClass = "bias-neutral";
    let labelText = "Neutral";

    if (bias === "strong_bullish") {
        labelClass = "bias-bullish";
        labelText = "Strong Bullish";
    } else if (bias === "bullish") {
        labelClass = "bias-bullish";
        labelText = "Bullish";
    } else if (bias === "strong_bearish") {
        labelClass = "bias-bearish";
        labelText = "Strong Bearish";
    } else if (bias === "bearish") {
        labelClass = "bias-bearish";
        labelText = "Bearish";
    }

    biasSummaryEl.innerHTML = "";

    const label = document.createElement("div");
    label.className = "bias-label";
    label.textContent = labelText;

    const scoreP = document.createElement("p");
    scoreP.textContent = `Bias score ${score.toFixed(2)}`;

    const tag = document.createElement("span");
    tag.className = `bias-tag ${labelClass}`;
    tag.textContent =
        data.premium_discount === "discount"
            ? "In discount"
            : data.premium_discount === "premium"
            ? "In premium"
            : "At equilibrium";

    const explList = document.createElement("ul");
    explanation.forEach(text => {
        const li = document.createElement("li");
        li.textContent = text;
        explList.appendChild(li);
    });

    biasSummaryEl.appendChild(label);
    biasSummaryEl.appendChild(scoreP);
    biasSummaryEl.appendChild(tag);
    if (explanation.length) {
        biasSummaryEl.appendChild(explList);
    }
}

function renderPremiumDiscount(data) {
    const fraction = data.discount_fraction;
    const zone = data.premium_discount;
    const percent = (fraction * 100).toFixed(1);

    const leftPercent = Math.max(0, Math.min(100, fraction * 100));
    pdFillEl.style.left = `${leftPercent}%`;

    let zoneText = "Equilibrium";
    if (zone === "discount") {
        zoneText = "Discount zone";
    } else if (zone === "premium") {
        zoneText = "Premium zone";
    }

    pdLabelEl.textContent = `${zoneText}  swing position ${percent}% from low to high`;
}

function renderDetails(data) {
    const liquidity = data.liquidity_levels || [];
    const fvgs = data.fair_value_gaps || [];
    const bos = data.bos_events || [];
    const choch = data.choch_events || [];
    const tradeSetups = data.trade_setups || [];

    detailsEl.innerHTML = "";
    const sections = [];

    const liqSection = document.createElement("div");
    liqSection.innerHTML = "<h3>Liquidity levels</h3>";
    const liqList = document.createElement("ul");
    if (!liquidity.length) {
        const li = document.createElement("li");
        li.textContent = "None detected in recent window";
        liqList.appendChild(li);
    } else {
        liquidity.slice(-10).forEach(l => {
            const li = document.createElement("li");
            li.textContent = `${l.type} at ${l.price.toFixed(2)}`;
            liqList.appendChild(li);
        });
    }
    liqSection.appendChild(liqList);
    sections.push(liqSection);

    const fvgSection = document.createElement("div");
    fvgSection.innerHTML = "<h3>Fair value gaps</h3>";
    const fvgList = document.createElement("ul");
    if (!fvgs.length) {
        const li = document.createElement("li");
        li.textContent = "None detected in recent window";
        fvgList.appendChild(li);
    } else {
        fvgs.slice(-10).forEach(f => {
            const li = document.createElement("li");
            li.textContent = `${f.type} gap ${f.gap_low.toFixed(2)} to ${f.gap_high.toFixed(2)}`;
            fvgList.appendChild(li);
        });
    }
    fvgSection.appendChild(fvgList);
    sections.push(fvgSection);

    const bosSection = document.createElement("div");
    bosSection.innerHTML = "<h3>Structure events</h3>";
    const bosList = document.createElement("ul");
    if (!bos.length) {
        const li = document.createElement("li");
        li.textContent = "No major structure breaks detected";
        bosList.appendChild(li);
    } else {
        bos.slice(-10).forEach(b => {
            const li = document.createElement("li");
            li.textContent = `${b.type} near ${b.price.toFixed(2)}`;
            bosList.appendChild(li);
        });
    }
    bosSection.appendChild(bosList);
    sections.push(bosSection);

    const chochSection = document.createElement("div");
    chochSection.innerHTML = "<h3>Change of character</h3>";
    const chochList = document.createElement("ul");
    if (!choch.length) {
        const li = document.createElement("li");
        li.textContent = "No CHoCH detected";
        chochList.appendChild(li);
    } else {
        choch.slice(-10).forEach(c => {
            const li = document.createElement("li");
            li.textContent = `${c.type} at ${c.price.toFixed(2)}`;
            chochList.appendChild(li);
        });
    }
    chochSection.appendChild(chochList);
    sections.push(chochSection);

    const tradesSection = document.createElement("div");
    tradesSection.innerHTML = "<h3>Trade setups</h3>";
    const tradeList = document.createElement("ul");

    if (!tradeSetups.length) {
        const li = document.createElement("li");
        li.textContent = "No clean setups based on current rules";
        tradeList.appendChild(li);
    } else {
        tradeSetups.forEach(t => {
            const li = document.createElement("li");
            li.innerHTML =
                `${t.direction.toUpperCase()} | ` +
                `Entry ${t.entry.toFixed(2)} | SL ${t.stop.toFixed(2)} | ` +
                `TP1 ${t.tp1.toFixed(2)} (R:R ${t.rr_tp1.toFixed(2)}) | ` +
                `TP2 ${t.tp2.toFixed(2)} (R:R ${t.rr_tp2.toFixed(2)})`;

            const sub = document.createElement("div");
            sub.className = "trade-notes";
            sub.textContent = (t.rationale || []).join("  ");
            li.appendChild(sub);

            tradeList.appendChild(li);
        });
    }

    tradesSection.appendChild(tradeList);
    sections.push(tradesSection);

    sections.forEach(s => detailsEl.appendChild(s));
}

function renderChart(data) {
    if (!chart) {
        createChart();
    }
    const ohlcv = data.ohlcv || [];
    if (!ohlcv.length) {
        return;
    }

    const candleData = ohlcv.map(c => ({
        time: new Date(c.time).getTime() / 1000,
        open: c.open,
        high: c.high,
        low: c.low,
        close: c.close,
    }));
    candleSeries.setData(candleData);

    const liquidity = data.liquidity_levels || [];
    const lastLiq = liquidity.length ? liquidity[liquidity.length - 1] : null;
    if (lastLiq) {
        const liqLine = candleData.map(c => ({
            time: c.time,
            value: lastLiq.price,
        }));
        liquiditySeries.setData(liqLine);
    } else {
        liquiditySeries.setData([]);
    }

    renderFvgs(data.fair_value_gaps || []);
    chart.timeScale().fitContent();
}

async function analyzeSample() {
    setStatus("Requesting analysis for sample data");
    try {
        const res = await fetch("/api/analyze/sample");
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Request failed");
        }
        const data = await res.json();
        setStatus("Sample analysis complete");
        renderBias(data);
        renderPremiumDiscount(data);
        renderDetails(data);
        renderChart(data);
    } catch (e) {
        setStatus(`Error  ${e.message}`);
    }
}

async function analyzeFile() {
    const file = fileInput.files[0];
    if (!file) {
        setStatus("Please choose a CSV file first");
        return;
    }
    setStatus("Uploading file and requesting analysis");
    const form = new FormData();
    form.append("file", file);
    try {
        const res = await fetch("/api/analyze/file", {
            method: "POST",
            body: form,
        });
        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Request failed");
        }
        const data = await res.json();
        setStatus("File analysis complete");
        renderBias(data);
        renderPremiumDiscount(data);
        renderDetails(data);
        renderChart(data);
    } catch (e) {
        setStatus(`Error  ${e.message}`);
    }
}

uploadBtn.addEventListener("click", analyzeFile);
sampleBtn.addEventListener("click", analyzeSample);

window.addEventListener("load", () => {
    createChart();
    setStatus("Ready. Upload a CSV or use sample data.");
});
