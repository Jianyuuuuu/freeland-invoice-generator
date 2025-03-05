document.addEventListener('DOMContentLoaded', function() {
    // Initialize date picker
    flatpickr('.date-picker', {
        dateFormat: 'Y-m-d',
        allowInput: true
    });
    
    // Set default date
    const today = new Date();
    const invoiceDatePicker = flatpickr('#invoice-date', {
        dateFormat: 'Y-m-d',
        defaultDate: today,
        allowInput: true
    });
    
    // 设置默认的Bill From值
    const defaultBillFrom = "Freeland Media Limited";
    const defaultAddressFrom = "Address：UNIT 1603, 16TH FLOOR, THE L.\nPLAZA 367 - 375 QUEEN'S ROAD\nCENTRAL SHEUNG WAN\nHONG KONG";
    const defaultLogoPath = "/static/uploads/logo_68d8aa16-dab3-4263-bcd2-5efe021a5416.png";
    
    // 设置默认值
    document.getElementById('bill-from').value = defaultBillFrom;
    document.getElementById('address-from').value = defaultAddressFrom;
    
    // 设置默认Logo
    if (defaultLogoPath) {
        const logoPreview = document.getElementById('logo-preview');
        const logoPath = document.getElementById('logo-path');
        
        // 检查Logo文件是否存在
        fetch(defaultLogoPath, { method: 'HEAD' })
            .then(response => {
                if (response.ok) {
                    // 显示Logo预览
                    logoPreview.innerHTML = '';
                    const img = document.createElement('img');
                    img.src = defaultLogoPath;
                    logoPreview.appendChild(img);
                    
                    // 保存Logo路径
                    logoPath.value = defaultLogoPath.replace('/static/', '');
                }
            })
            .catch(error => {
                console.error('Logo not found:', error);
            });
    }
    
    // Logo upload functionality
    const logoPreview = document.getElementById('logo-preview');
    const logoUpload = document.getElementById('logo-upload');
    const logoPath = document.getElementById('logo-path');
    
    logoPreview.addEventListener('click', function() {
        logoUpload.click();
    });
    
    logoPreview.addEventListener('dragover', function(e) {
        e.preventDefault();
        logoPreview.style.borderColor = '#3498db';
    });
    
    logoPreview.addEventListener('dragleave', function() {
        logoPreview.style.borderColor = '#ccc';
    });
    
    logoPreview.addEventListener('drop', function(e) {
        e.preventDefault();
        logoPreview.style.borderColor = '#ccc';
        
        if (e.dataTransfer.files.length > 0) {
            handleLogoFile(e.dataTransfer.files[0]);
        }
    });
    
    logoUpload.addEventListener('change', function() {
        if (logoUpload.files.length > 0) {
            handleLogoFile(logoUpload.files[0]);
        }
    });
    
    function handleLogoFile(file) {
        // Check file type
        if (!file.type.match('image.*')) {
            alert('Please select an image file');
            return;
        }
        
        // Upload Logo
        const formData = new FormData();
        formData.append('logo', file);
        
        fetch('/upload_logo', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show Logo preview
                logoPreview.innerHTML = '';
                const img = document.createElement('img');
                img.src = '/static/' + data.logo_path;
                logoPreview.appendChild(img);
                
                // Save Logo path
                logoPath.value = data.logo_path;
            } else {
                alert('Failed to upload logo: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Logo upload error:', error);
            alert('Failed to upload logo, please try again');
        });
    }
    
    // Items table functionality
    const itemsTable = document.querySelector('#items-table tbody');
    const addItemBtn = document.getElementById('add-item');
    
    // Add event listeners for existing row
    const initialRow = itemsTable.querySelector('.item-row');
    const initialQtyInput = initialRow.querySelector('.item-qty');
    const initialPriceInput = initialRow.querySelector('.item-price');
    const initialRemoveBtn = initialRow.querySelector('.remove-item');
    
    initialQtyInput.addEventListener('input', updateRowAmount);
    initialPriceInput.addEventListener('input', updateRowAmount);
    initialRemoveBtn.addEventListener('click', removeItemRow);
    
    // Add new row button
    addItemBtn.addEventListener('click', addItemRow);
    
    // 添加项目行
    function addItemRow() {
        const tbody = document.querySelector('#items-table tbody');
        const newRow = document.createElement('tr');
        newRow.className = 'item-row';
        
        newRow.innerHTML = `
            <td><input type="text" class="item-name" placeholder="Item name"></td>
            <td class="qty-col"><input type="number" class="item-qty" value="0" min="0"></td>
            <td class="price-col"><input type="number" class="item-price" value="0" min="0" step="0.01"></td>
            <td class="item-amount">$0.00</td>
            <td><button type="button" class="remove-item">×</button></td>
        `;
        
        tbody.appendChild(newRow);
        
        // 添加事件监听器
        const qtyInput = newRow.querySelector('.item-qty');
        const priceInput = newRow.querySelector('.item-price');
        const removeBtn = newRow.querySelector('.remove-item');
        
        qtyInput.addEventListener('input', updateRowAmount);
        priceInput.addEventListener('input', updateRowAmount);
        removeBtn.addEventListener('click', removeItemRow);
    }
    
    // 移除项目行
    function removeItemRow(e) {
        const row = e.target.closest('.item-row');
        row.parentNode.removeChild(row);
        updateTotals();
    }
    
    // 更新行金额
    function updateRowAmount(e) {
        const row = e.target.closest('.item-row');
        const quantity = parseFloat(row.querySelector('.item-qty').value) || 0;
        const price = parseFloat(row.querySelector('.item-price').value) || 0;
        const amount = quantity * price;
        
        // 格式化金额显示，与PDF输出一致
        row.querySelector('.item-amount').textContent = '$' + amount.toFixed(2);
        
        updateTotals();
    }
    
    // 更新总计
    function updateTotals() {
        let subtotal = 0;
        const itemRows = document.querySelectorAll('.item-row');
        
        itemRows.forEach(row => {
            const quantity = parseFloat(row.querySelector('.item-qty').value) || 0;
            const price = parseFloat(row.querySelector('.item-price').value) || 0;
            subtotal += quantity * price;
        });
        
        const taxRate = showTaxCheckbox.checked ? parseFloat(document.getElementById('tax-rate').value) || 0 : 0;
        const taxAmount = subtotal * (taxRate / 100);
        const total = subtotal + taxAmount;
        
        // 格式化金额显示，与PDF输出一致
        document.getElementById('subtotal').textContent = '$' + subtotal.toFixed(2);
        document.getElementById('tax-amount').textContent = '$' + taxAmount.toFixed(2);
        document.getElementById('total-amount').textContent = '$' + total.toFixed(2);
    }
    
    // Tax rate input
    const taxRateInput = document.getElementById('tax-rate');
    taxRateInput.addEventListener('input', updateTotals);
    
    // Document type select
    const documentTypeSelect = document.getElementById('document-type');
    documentTypeSelect.addEventListener('change', function() {
        const documentTitle = document.getElementById('document-title');
        documentTitle.textContent = documentTypeSelect.value === 'receipt' ? 'Receipt' : 'Invoice';
    });
    
    // Settings
    const showTaxCheckbox = document.getElementById('show-tax');
    const showNotesCheckbox = document.getElementById('show-notes');
    const taxSection = document.querySelector('.total-row:nth-child(2)');
    const notesSection = document.querySelector('.notes-section');
    
    // Initialize settings
    updateTaxVisibility();
    updateNotesVisibility();
    
    // Add event listeners for settings
    showTaxCheckbox.addEventListener('change', updateTaxVisibility);
    showNotesCheckbox.addEventListener('change', updateNotesVisibility);
    
    function updateTaxVisibility() {
        taxSection.style.display = showTaxCheckbox.checked ? 'flex' : 'none';
        updateTotals();
    }
    
    function updateNotesVisibility() {
        notesSection.style.display = showNotesCheckbox.checked ? 'block' : 'none';
    }
    
    // Preview button
    const previewBtn = document.getElementById('preview-btn');
    const previewModal = document.getElementById('preview-modal');
    const closeBtn = previewModal.querySelector('.close');
    const pdfPreview = document.getElementById('pdf-preview');
    const loadingOverlay = document.getElementById('loading-overlay');
    
    previewBtn.addEventListener('click', function() {
        generatePDF('preview');
    });
    
    closeBtn.addEventListener('click', function() {
        previewModal.style.display = 'none';
        // 清空iframe内容，防止重复加载
        pdfPreview.src = '';
    });
    
    window.addEventListener('click', function(e) {
        if (e.target === previewModal) {
            previewModal.style.display = 'none';
            // 清空iframe内容，防止重复加载
            pdfPreview.src = '';
        }
    });
    
    // Download button
    const downloadBtn = document.getElementById('download-btn');
    
    downloadBtn.addEventListener('click', function() {
        generatePDF('download');
    });
    
    // Generate PDF
    function generatePDF(action) {
        // Collect form data
        const documentType = documentTypeSelect.value;
        const invoiceData = {
            document_type: documentType,
            invoice_number: document.getElementById('invoice-number').value,
            invoice_date: document.getElementById('invoice-date').value,
            bill_from: document.getElementById('bill-from').value,
            address_from: document.getElementById('address-from').value,
            bill_to: document.getElementById('bill-to').value,
            address_to: document.getElementById('address-to').value,
            logo_path: document.getElementById('logo-path').value,
            tax_rate: showTaxCheckbox.checked ? parseFloat(document.getElementById('tax-rate').value) || 0 : 0,
            show_tax: showTaxCheckbox.checked,
            show_notes: showNotesCheckbox.checked,
            notes: document.getElementById('notes').value,
            items: [],
            action: action // 添加action参数，告诉后端是预览还是下载
        };
        
        // Collect items data
        const itemRows = document.querySelectorAll('.item-row');
        itemRows.forEach(row => {
            const name = row.querySelector('.item-name').value;
            const quantity = parseFloat(row.querySelector('.item-qty').value) || 0;
            const price = parseFloat(row.querySelector('.item-price').value) || 0;
            
            if (name || quantity > 0 || price > 0) {
                invoiceData.items.push({
                    name: name,
                    quantity: quantity,
                    price: price
                });
            }
        });
        
        // Show loading overlay
        loadingOverlay.style.display = 'flex';
        
        // Send request to generate PDF
        fetch('/generate_pdf', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(invoiceData)
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading overlay
            loadingOverlay.style.display = 'none';
            
            if (data.success) {
                if (action === 'preview') {
                    // 显示预览模态框
                    previewModal.style.display = 'block';
                    // 设置iframe的src为PDF URL
                    pdfPreview.src = data.pdf_url + '?t=' + new Date().getTime(); // 添加时间戳防止缓存
                } else if (action === 'download') {
                    // 下载文件
                    window.location.href = data.pdf_url;
                }
            } else {
                alert('Failed to generate PDF: ' + data.error);
            }
        })
        .catch(error => {
            // Hide loading overlay
            loadingOverlay.style.display = 'none';
            console.error('PDF generation error:', error);
            alert('Failed to generate PDF, please try again');
        });
    }
}); 