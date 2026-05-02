/**
 * LPR 分段利息计算器核心逻辑
 */

/**
 * 计算两个日期之间的天数
 * @param {string} startDate - 开始日期
 * @param {string} endDate - 结束日期
 * @param {boolean} includeEndDay - 是否包含止息日（算头算尾）
 * @returns {number} 天数
 */
function getDaysDiff(startDate, endDate, includeEndDay = true) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = end - start;
    const days = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return includeEndDay ? days + 1 : days;
}

/**
 * 切换高级设置显示
 */
function toggleSettings() {
    const section = document.getElementById('settingsSection');
    section.classList.toggle('hidden');
}

/**
 * 添加还款记录行
 */
function addRepaymentRow() {
    const container = document.getElementById('repaymentList');
    const row = document.createElement('div');
    row.className = 'repayment-row';
    row.style.cssText = 'display: flex; gap: 10px; margin-bottom: 10px; align-items: center;';

    row.innerHTML = `
        <input type="date" class="repayment-date" style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <input type="number" class="repayment-amount" placeholder="还款金额" style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
        <select class="repayment-type" style="flex: 0.8; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
            <option value="principal">还本金</option>
            <option value="interest">还利息</option>
        </select>
        <button type="button" onclick="this.parentElement.remove()" style="background: #ff4444; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer;">删除</button>
    `;

    // 设置默认日期为今天
    const today = new Date().toISOString().slice(0, 10);
    row.querySelector('.repayment-date').value = today;

    container.appendChild(row);
}

/**
 * 获取所有还款记录
 */
function getRepayments() {
    const rows = document.querySelectorAll('.repayment-row');
    const repayments = [];

    rows.forEach(row => {
        const date = row.querySelector('.repayment-date').value;
        const amount = parseFloat(row.querySelector('.repayment-amount').value);
        const type = row.querySelector('.repayment-type').value;

        if (date && !isNaN(amount) && amount > 0) {
            repayments.push({ date, amount, type });
        }
    });

    // 按日期排序
    repayments.sort((a, b) => new Date(a.date) - new Date(b.date));

    return repayments;
}

/**
 * 获取计算设置
 */
function getCalculationSettings() {
    const countEndDay = document.querySelector('input[name="countEndDay"]:checked').value;
    const yearDays = parseInt(document.querySelector('input[name="yearDays"]:checked').value);
    const useStartDateLPR = document.getElementById('useStartDateLPR').checked;
    const coefficient = parseFloat(document.getElementById('interestCoefficient').value) || 1;

    return {
        includeEndDay: countEndDay === 'include',
        yearDays: yearDays,
        useStartDateLPR: useStartDateLPR,
        coefficient: coefficient
    };
}

/**
 * 格式化日期显示
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
}

/**
 * 格式化金额
 */
function formatMoney(amount) {
    return '¥' + amount.toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * 获取 LPR 数据（优先使用用户自定义数据）
 */
function getLPRData() {
    const saved = localStorage.getItem('lprData');
    if (saved) {
        return JSON.parse(saved);
    }
    return LPR_DATA;
}

/**
 * 获取日期范围内的有效 LPR 利率段
 * 原则：LPR 发布当日及之后适用新利率
 * @param {string} startDate - 开始日期
 * @param {string} endDate - 结束日期
 * @param {string} lprType - LPR类型
 * @param {boolean} includeEndDay - 是否包含止息日
 * @param {boolean} useStartDateLPR - 是否使用起始日LPR（不分段）
 */
function getLPRSegments(startDate, endDate, lprType, includeEndDay = true, useStartDateLPR = false) {
    const lprDataSource = getLPRData();
    const lprData = lprDataSource[lprType] || lprDataSource['1year'];
    const segments = [];

    const start = new Date(startDate);
    const end = new Date(endDate);

    // 找到起始日期适用的利率（找到最后一个发布日期 <= 起息日的利率）
    let startRate = null;
    let startRateDate = null;

    for (let i = 0; i < lprData.length; i++) {
        const lprDate = new Date(lprData[i].date);
        if (lprDate <= start) {
            startRate = lprData[i].rate;
            startRateDate = lprData[i].date;
        }
    }

    // 如果没有找到适用利率（起息日早于最早 LPR 数据）
    if (startRate === null) {
        startRate = lprData[0].rate;
        startRateDate = lprData[0].date;
    }

    // 如果选择"按起始日适用的LPR计算"，则整个期间使用起始日的利率，不分段
    if (useStartDateLPR) {
        segments.push({
            startDate: new Date(start),
            endDate: new Date(end),
            rate: startRate,
            lprSource: startRateDate,
            days: getDaysDiff(start, end, includeEndDay)
        });
        return segments;
    }

    // 正常分段计算
    let currentRate = startRate;
    let currentRateDate = startRateDate;
    let currentSegmentStart = new Date(start);

    // 遍历 LPR 数据，找出所有需要分段的区间
    for (let i = 0; i < lprData.length; i++) {
        const lprDate = new Date(lprData[i].date);

        // LPR 发布日期在起息日之后且在止息日之前，需要分段
        if (lprDate > start && lprDate <= end) {
            // 结束当前段（到 LPR 发布日前一天）
            const segmentEnd = new Date(lprDate);
            segmentEnd.setDate(segmentEnd.getDate() - 1);

            segments.push({
                startDate: new Date(currentSegmentStart),
                endDate: segmentEnd,
                rate: currentRate,
                lprSource: currentRateDate,
                days: getDaysDiff(currentSegmentStart, segmentEnd, includeEndDay)
            });

            // 开始新段（从 LPR 发布日当天）
            currentSegmentStart = new Date(lprDate);
            currentRate = lprData[i].rate;
            currentRateDate = lprData[i].date;
        }
    }

    // 添加最后一段
    segments.push({
        startDate: currentSegmentStart,
        endDate: new Date(end),
        rate: currentRate,
        lprSource: currentRateDate,
        days: getDaysDiff(currentSegmentStart, end, includeEndDay)
    });

    return segments;
}

/**
 * 计算分段利息
 * 公式：利息 = 本金 × 利率 × 天数 ÷ 年天数基准
 * @param {number} principal - 本金
 * @param {number} rate - 利率(%)
 * @param {number} days - 天数
 * @param {number} yearDays - 年天数基准(360或365)
 * @param {number} coefficient - 利息系数
 * @returns {number} 利息金额
 */
function calculateSegmentInterest(principal, rate, days, yearDays = 365, coefficient = 1) {
    const interest = principal * (rate / 100) * days / yearDays;
    return interest * coefficient;
}

/**
 * 获取完整的分段（包含LPR变化日期和还款日期）
 */
function getCompleteSegments(startDate, endDate, lprType, repayments, includeEndDay) {
    const lprDataSource = getLPRData();
    const lprData = lprDataSource[lprType] || lprDataSource['1year'];
    const segments = [];

    const start = new Date(startDate);
    const end = new Date(endDate);

    // 找到起始日期适用的利率
    let startRate = null;
    let startRateDate = null;
    for (let i = 0; i < lprData.length; i++) {
        const lprDate = new Date(lprData[i].date);
        if (lprDate <= start) {
            startRate = lprData[i].rate;
            startRateDate = lprData[i].date;
        }
    }
    if (startRate === null) {
        startRate = lprData[0].rate;
        startRateDate = lprData[0].date;
    }

    // 收集所有分段点（LPR变化日期 + 还款日期）
    const breakPoints = [];

    // 添加LPR变化日期
    for (let i = 0; i < lprData.length; i++) {
        const lprDate = new Date(lprData[i].date);
        if (lprDate > start && lprDate <= end) {
            breakPoints.push({
                date: lprDate,
                type: 'lpr',
                rate: lprData[i].rate,
                lprSource: lprData[i].date
            });
        }
    }

    // 添加还款日期
    repayments.forEach(repayment => {
        const repayDate = new Date(repayment.date);
        if (repayDate >= start && repayDate <= end) {
            breakPoints.push({
                date: repayDate,
                type: 'repayment',
                repayment: repayment
            });
        }
    });

    // 按日期排序
    breakPoints.sort((a, b) => a.date - b.date);

    // 生成分段
    let currentSegmentStart = new Date(start);
    let currentRate = startRate;
    let currentRateDate = startRateDate;

    for (let i = 0; i < breakPoints.length; i++) {
        const point = breakPoints[i];

        if (point.type === 'repayment') {
            // 还款日：算到还款日当天（然后处理还款）
            const days = getDaysDiff(currentSegmentStart, point.date, includeEndDay);
            if (days > 0) {
                segments.push({
                    startDate: new Date(currentSegmentStart),
                    endDate: new Date(point.date),
                    rate: currentRate,
                    lprSource: currentRateDate,
                    days: days,
                    repaymentAtEnd: point.repayment
                });
            }
            // 从还款日次日开始新段
            currentSegmentStart = new Date(point.date);
            currentSegmentStart.setDate(currentSegmentStart.getDate() + 1);
        } else {
            // LPR变化日
            // LPR变化日：算到变化日前一天
            const dayBefore = new Date(point.date);
            dayBefore.setDate(dayBefore.getDate() - 1);
            const days = getDaysDiff(currentSegmentStart, dayBefore, includeEndDay);
            if (days > 0) {
                segments.push({
                    startDate: new Date(currentSegmentStart),
                    endDate: dayBefore,
                    rate: currentRate,
                    lprSource: currentRateDate,
                    days: days,
                    repaymentAtEnd: null
                });
            }
            // 从LPR变化日当天开始新段
            currentSegmentStart = new Date(point.date);
            currentRate = point.rate;
            currentRateDate = point.lprSource;
        }
    }

    // 添加最后一段
    if (currentSegmentStart <= end) {
        segments.push({
            startDate: currentSegmentStart,
            endDate: new Date(end),
            rate: currentRate,
            lprSource: currentRateDate,
            days: getDaysDiff(currentSegmentStart, end, includeEndDay),
            repaymentAtEnd: null
        });
    }

    return segments;
}

/**
 * 主计算函数
 */
function calculate() {
    // 获取输入值
    const principal = parseFloat(document.getElementById('principal').value);
    const startDate = document.getElementById('startDate').value;
    const endDate = document.getElementById('endDate').value;
    const lprType = document.getElementById('lprType').value;

    // 验证输入
    if (!principal || principal <= 0) {
        alert('请输入有效的本金金额');
        return;
    }
    if (!startDate) {
        alert('请选择起息日');
        return;
    }
    if (!endDate) {
        alert('请选择止息日');
        return;
    }
    if (new Date(startDate) > new Date(endDate)) {
        alert('起息日不能晚于止息日');
        return;
    }

    // 获取计算设置
    const settings = getCalculationSettings();

    // 获取还款记录
    const repayments = getRepayments();

    // 验证还款日期
    for (const repayment of repayments) {
        const repayDate = new Date(repayment.date);
        if (repayDate < new Date(startDate) || repayDate > new Date(endDate)) {
            alert(`还款日期 ${repayment.date} 必须在起息日和止息日之间`);
            return;
        }
    }

    // 获取完整分段
    let segments;
    if (settings.useStartDateLPR) {
        // 按起始日LPR计算（不分段LPR变化）
        segments = getLPRSegments(startDate, endDate, lprType, settings.includeEndDay, true);
    } else {
        // 正常分段计算（含还款）
        segments = getCompleteSegments(startDate, endDate, lprType, repayments, settings.includeEndDay);
    }

    // 计算每段利息
    let totalInterest = 0;
    let totalDays = 0;
    let currentPrincipal = principal;
    let totalPrincipalRepaid = 0;
    let totalInterestRepaid = 0;
    let remainingPrincipal = principal;

    const segmentsWithDetails = [];

    segments.forEach((seg, index) => {
        // 计算该段利息（按当前本金）
        const interest = calculateSegmentInterest(currentPrincipal, seg.rate, seg.days, settings.yearDays, settings.coefficient);
        totalInterest += interest;
        totalDays += seg.days;

        const segmentDetail = {
            ...seg,
            index: index + 1,
            interest: interest,
            principalAtStart: currentPrincipal,
            principalRepaid: 0,
            interestRepaid: 0
        };

        // 处理该段结束时的还款
        if (seg.repaymentAtEnd) {
            const repayment = seg.repaymentAtEnd;
            if (repayment.type === 'principal') {
                // 还本金
                const principalRepaid = Math.min(repayment.amount, currentPrincipal);
                currentPrincipal -= principalRepaid;
                totalPrincipalRepaid += principalRepaid;
                segmentDetail.principalRepaid = principalRepaid;
                segmentDetail.remainingPrincipal = currentPrincipal;
                remainingPrincipal = currentPrincipal;
            } else {
                // 还利息
                totalInterestRepaid += repayment.amount;
                segmentDetail.interestRepaid = repayment.amount;
            }
            segmentDetail.repaymentInfo = repayment;
        }

        segmentsWithDetails.push(segmentDetail);
    });

    // 计算平均利率
    const avgRate = totalInterest > 0
        ? (totalInterest / settings.coefficient * settings.yearDays / totalDays / principal * 100).toFixed(2)
        : 0;

    // 显示结果
    displayResults({
        principal,
        totalInterest,
        totalDays,
        avgRate,
        segments: segmentsWithDetails,
        settings: settings,
        repayments: {
            totalPrincipalRepaid,
            totalInterestRepaid,
            remainingPrincipal
        }
    });
}

/**
 * 显示计算结果
 */
function displayResults(result) {
    // 隐藏空状态，显示结果区域
    document.getElementById('emptyState').classList.add('hidden');
    document.getElementById('resultSection').classList.remove('hidden');

    // 更新汇总卡片
    document.getElementById('totalInterest').textContent = formatMoney(result.totalInterest);
    document.getElementById('summaryPrincipal').textContent = formatMoney(result.principal);
    document.getElementById('summaryDays').textContent = result.totalDays + '天';
    document.getElementById('avgRate').textContent = result.avgRate + '%';

    // 如果有还款，显示还款信息
    const repayInfo = result.repayments;
    if (repayInfo && (repayInfo.totalPrincipalRepaid > 0 || repayInfo.totalInterestRepaid > 0)) {
        // 添加或更新还款信息区域
        let repayDiv = document.getElementById('repaymentSummary');
        if (!repayDiv) {
            repayDiv = document.createElement('div');
            repayDiv.id = 'repaymentSummary';
            repayDiv.className = 'summary-details';
            repayDiv.style.marginTop = '15px';
            repayDiv.style.paddingTop = '15px';
            repayDiv.style.borderTop = '1px solid rgba(255,255,255,0.3)';
            document.querySelector('.summary-card').appendChild(repayDiv);
        }

        let repayHtml = '';
        if (repayInfo.totalPrincipalRepaid > 0) {
            repayHtml += `
                <div class="summary-item">
                    <span>已还本金</span>
                    <strong>${formatMoney(repayInfo.totalPrincipalRepaid)}</strong>
                </div>
            `;
        }
        if (repayInfo.totalInterestRepaid > 0) {
            repayHtml += `
                <div class="summary-item">
                    <span>已还利息</span>
                    <strong>${formatMoney(repayInfo.totalInterestRepaid)}</strong>
                </div>
            `;
        }
        if (repayInfo.remainingPrincipal !== result.principal) {
            repayHtml += `
                <div class="summary-item">
                    <span>剩余本金</span>
                    <strong>${formatMoney(repayInfo.remainingPrincipal)}</strong>
                </div>
            `;
        }
        repayDiv.innerHTML = repayHtml;
    }

    // 更新明细表格
    const tbody = document.getElementById('segmentsBody');
    tbody.innerHTML = '';

    result.segments.forEach(seg => {
        const row = document.createElement('tr');

        // 构建还款标记
        let repaymentMark = '';
        if (seg.repaymentInfo) {
            const typeText = seg.repaymentInfo.type === 'principal' ? '还本金' : '还利息';
            repaymentMark = `<span style="color: #ff6600; font-size: 12px;">(${typeText} ${formatMoney(seg.repaymentInfo.amount)})</span>`;
        }

        row.innerHTML = `
            <td>${seg.index}</td>
            <td>${formatDate(seg.startDate)}${seg.repaymentInfo && seg.repaymentInfo.type === 'principal' ? '<br><small>本金:' + formatMoney(seg.principalAtStart) + '</small>' : ''}</td>
            <td>${formatDate(seg.endDate)} ${repaymentMark}</td>
            <td>${seg.days}</td>
            <td class="rate-display">${seg.rate.toFixed(2)}%</td>
            <td>${seg.lprSource}</td>
            <td class="interest-display">${formatMoney(seg.interest)}</td>
        `;
        tbody.appendChild(row);
    });

    // 滚动到结果区域
    document.getElementById('resultSection').scrollIntoView({ behavior: 'smooth' });

    // 保存计算结果供导出使用
    window.lastCalculationResult = result;
    window.lastCalculationInputs = {
        principal: parseFloat(document.getElementById('principal').value),
        startDate: document.getElementById('startDate').value,
        endDate: document.getElementById('endDate').value,
        lprType: document.getElementById('lprType').value,
        lprTypeName: document.getElementById('lprType').options[document.getElementById('lprType').selectedIndex].text,
        settings: result.settings,
        repayments: result.repayments
    };
}

/**
 * 检查是否需要更新 LPR 数据（打开时）
 * 只在最新数据超过30天未更新时才提示
 */
function checkLPRDataUpdate() {
    const lastCheck = localStorage.getItem('lprLastCheckDate');
    const today = new Date().toISOString().slice(0, 10);

    // 如果今天已经检查过，不再提示
    if (lastCheck === today) {
        return;
    }

    // 获取当前数据
    const lprData = getLPRData();
    let latestDate = '';

    // 找到最新的 LPR 发布日期
    if (lprData['1year'] && lprData['1year'].length > 0) {
        latestDate = lprData['1year'][lprData['1year'].length - 1].date;
    }

    // 计算最新数据距今多少天
    let daysSinceLastUpdate = 0;
    if (latestDate) {
        const lastUpdate = new Date(latestDate);
        const now = new Date();
        daysSinceLastUpdate = Math.floor((now - lastUpdate) / (1000 * 60 * 60 * 24));
    }

    // 记录今天已检查
    localStorage.setItem('lprLastCheckDate', today);

    // 只有当最新数据超过30天，或者没有数据时，才提示更新
    const needsUpdate = !latestDate || daysSinceLastUpdate > 30;

    if (!needsUpdate) {
        console.log(`LPR 数据最新日期：${latestDate}，距今 ${daysSinceLastUpdate} 天，无需更新`);
        return;
    }

    // 显示更新提示
    const message = latestDate
        ? `当前 LPR 数据最新至 ${latestDate}，距今已超过 ${daysSinceLastUpdate} 天，建议更新。\n\n是否前往更新 LPR 数据？`
        : '尚未配置 LPR 数据，是否需要更新？';

    // 使用 setTimeout 延迟显示，避免页面加载时立即弹出
    setTimeout(() => {
        if (confirm(message)) {
            // 用户选择更新，跳转到数据管理页面
            window.location.href = 'data-manager.html';
        }
    }, 500);
}

// 设置默认日期（起息日：一年前，止息日：今天）
document.addEventListener('DOMContentLoaded', function() {
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);

    document.getElementById('endDate').value = formatDate(today);
    document.getElementById('startDate').value = formatDate(oneYearAgo);

    // 检查是否需要更新 LPR 数据
    checkLPRDataUpdate();
});

/**
 * 导出 Excel 报表
 */
function exportToExcel() {
    // 检查是否有计算结果
    if (!window.lastCalculationResult || !window.lastCalculationInputs) {
        alert('请先进行利息计算，再导出报表');
        return;
    }

    const { principal, startDate, endDate, lprTypeName, settings, repayments } = window.lastCalculationInputs;
    const { totalInterest, totalDays, avgRate, segments } = window.lastCalculationResult;

    // 生成文件名
    const timestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const filename = `LPR利息计算表_${timestamp}.xlsx`;

    // 计算设置描述
    const countMethodText = settings.includeEndDay ? '算头算尾' : '算头不算尾';
    const lprMethodText = settings.useStartDateLPR ? '按起始日LPR计算（不分段）' : '分段计算';

    // 准备汇总数据
    const summaryData = [
        ['LPR 分段利息计算表'],
        [''],
        ['基本信息'],
        ['本金金额', formatMoney(principal)],
        ['LPR类型', lprTypeName],
        ['起息日', startDate],
        ['止息日', endDate],
        [''],
        ['计算设置'],
        ['计息方式', countMethodText],
        ['年天数基准', settings.yearDays + '天'],
        ['LPR计算方式', lprMethodText],
        ['利息系数', settings.coefficient],
        [''],
        ['汇总结果'],
        ['利息总额', formatMoney(totalInterest)],
        ['计息天数', totalDays + '天'],
        ['平均年利率', avgRate + '%']
    ];

    // 添加还款信息（如果有）
    if (repayments && (repayments.totalPrincipalRepaid > 0 || repayments.totalInterestRepaid > 0)) {
        summaryData.push(['']);
        summaryData.push(['还款信息']);
        if (repayments.totalPrincipalRepaid > 0) {
            summaryData.push(['已还本金', formatMoney(repayments.totalPrincipalRepaid)]);
        }
        if (repayments.totalInterestRepaid > 0) {
            summaryData.push(['已还利息', formatMoney(repayments.totalInterestRepaid)]);
        }
        if (repayments.remainingPrincipal !== principal) {
            summaryData.push(['剩余本金', formatMoney(repayments.remainingPrincipal)]);
        }
    }

    summaryData.push(['']);
    summaryData.push(['分段计算明细']);
    summaryData.push(['序号', '开始日期', '结束日期', '计息本金', '天数', '适用利率', 'LPR数据出处', '分段利息', '还款备注']);

    // 添加明细数据
    segments.forEach(seg => {
        let repaymentNote = '';
        if (seg.repaymentInfo) {
            const typeText = seg.repaymentInfo.type === 'principal' ? '还本金' : '还利息';
            repaymentNote = `${typeText} ${formatMoney(seg.repaymentInfo.amount)}`;
        }

        summaryData.push([
            seg.index,
            formatDate(seg.startDate),
            formatDate(seg.endDate),
            formatMoney(seg.principalAtStart || principal),
            seg.days,
            seg.rate.toFixed(4) + '%',
            seg.lprSource,
            seg.interest.toFixed(2),
            repaymentNote
        ]);
    });

    // 创建汇总工作表
    const ws = XLSX.utils.aoa_to_sheet(summaryData);

    // 设置列宽
    ws['!cols'] = [
        { wch: 10 },  // 序号
        { wch: 15 },  // 开始日期
        { wch: 15 },  // 结束日期
        { wch: 15 },  // 计息本金
        { wch: 10 },  // 天数
        { wch: 12 },  // 适用利率
        { wch: 15 },  // LPR数据出处
        { wch: 12 },  // 分段利息
        { wch: 20 }   // 还款备注
    ];

    // 计算合并单元格的行号
    let mergeRow = 15;
    if (repayments && (repayments.totalPrincipalRepaid > 0 || repayments.totalInterestRepaid > 0)) {
        mergeRow += 5;  // 还款信息增加了5行
    }

    // 合并标题单元格
    const merges = [
        { s: { r: 0, c: 0 }, e: { r: 0, c: 8 } },   // 主标题
        { s: { r: 2, c: 0 }, e: { r: 2, c: 8 } },   // 基本信息标题
        { s: { r: 9, c: 0 }, e: { r: 9, c: 8 } },   // 计算设置标题
        { s: { r: 15, c: 0 }, e: { r: 15, c: 8 } }  // 汇总结果标题
    ];

    // 如果有还款信息，添加还款信息标题合并
    if (repayments && (repayments.totalPrincipalRepaid > 0 || repayments.totalInterestRepaid > 0)) {
        merges.push({ s: { r: 17, c: 0 }, e: { r: 17, c: 8 } });  // 还款信息标题
    }

    ws['!merges'] = merges;

    // 创建工作簿
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, '计算结果');

    // 导出文件
    XLSX.writeFile(wb, filename);
}
