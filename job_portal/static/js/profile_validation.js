// Client-side form validation
function validateForm() {
    let isValid = true;
    const errors = [];
    
    // Helper to add error message
    const addError = (field, message) => {
        const input = document.getElementById(field);
        if (input) {
            input.classList.add('is-invalid');
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'invalid-feedback';
            feedbackDiv.textContent = message;
            input.parentNode.appendChild(feedbackDiv);
        }
        errors.push(message);
        isValid = false;
    };

    // Helper to validate required field
    const validateRequired = (field, fieldName) => {
        const input = document.getElementById(field);
        if (!input?.value?.trim()) {
            addError(field, `${fieldName} is required`);
        }
    };

    // Clear previous errors
    document.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
    document.querySelectorAll('.invalid-feedback').forEach(el => el.remove());

    // Basic Information
    validateRequired('bio', 'Bio');
    validateRequired('phone', 'Phone number');
    validateRequired('location', 'Location');

    // Phone number format validation
    const phone = document.getElementById('phone').value;
    if (phone && !/^\+?[\d\s-]{10,}$/.test(phone)) {
        addError('phone', 'Please enter a valid phone number');
    }

    // Profile picture validation
    const profilePicInput = document.getElementById('profile-picture-input');
    if (profilePicInput.files.length > 0) {
        const file = profilePicInput.files[0];
        const maxSize = 5 * 1024 * 1024; // 5MB
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];

        if (file.size > maxSize) {
            addError('profile-picture-input', 'Profile picture must be less than 5MB');
        }
        
        if (!allowedTypes.includes(file.type)) {
            addError('profile-picture-input', 'Only JPG, PNG, and GIF files are allowed');
        }
    }

    // User type specific validation
    const userType = document.querySelector('input[name="user_type"]')?.value;
    
    if (userType === 'employer') {
        validateRequired('company_name', 'Company name');
        validateRequired('about_company', 'Company description');
        
        // Website URL validation
        const website = document.getElementById('company_website').value;
        if (website && !/^https?:\/\/.+\..+/.test(website)) {
            addError('company_website', 'Please enter a valid website URL starting with http:// or https://');
        }
        
        // Number of employees validation
        const employees = document.getElementById('number_of_employees').value;
        if (employees && (isNaN(employees) || parseInt(employees) < 1)) {
            addError('number_of_employees', 'Number of employees must be a positive number');
        }
    } else {
        validateRequired('skills', 'Skills');
        
        // Experience validation
        const expTitles = document.querySelectorAll('input[name="experience_title[]"]');
        const expDescs = document.querySelectorAll('textarea[name="experience_description[]"]');
        
        expTitles.forEach((title, index) => {
            if (title.value.trim() && !expDescs[index].value.trim()) {
                addError(expDescs[index].id, 'Experience description is required');
            }
            if (!title.value.trim() && expDescs[index].value.trim()) {
                addError(title.id, 'Experience title is required');
            }
        });
        
        // Education validation
        const eduDegrees = document.querySelectorAll('input[name="education_degree[]"]');
        const eduDescs = document.querySelectorAll('textarea[name="education_description[]"]');
        
        eduDegrees.forEach((degree, index) => {
            if (degree.value.trim() && !eduDescs[index].value.trim()) {
                addError(eduDescs[index].id, 'Education description is required');
            }
            if (!degree.value.trim() && eduDescs[index].value.trim()) {
                addError(degree.id, 'Degree title is required');
            }
        });
    }

    // Display all errors at the top if any
    if (errors.length > 0) {
        const errorContainer = document.getElementById('form-errors');
        errorContainer.innerHTML = '<div class="alert alert-danger"><ul class="mb-0">' + 
            errors.map(error => `<li>${error}</li>`).join('') + 
            '</ul></div>';
        errorContainer.scrollIntoView({ behavior: 'smooth' });
    }

    return isValid;
}

// Show loading state
function showLoading() {
    const submitBtn = document.querySelector('.btn-update');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Updating...';
}

// Initialize form
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (validateForm()) {
            showLoading();
            form.submit();
        }
    });

    // Add custom validation classes on input
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('input', function() {
            this.classList.remove('is-invalid');
            const feedback = this.parentNode.querySelector('.invalid-feedback');
            if (feedback) feedback.remove();
        });
    });
});
