const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

const toast = (title, message) => {
  $('#toast strong').textContent = title;
  $('#toast small').textContent = message;
  $('#toast').classList.add('show');
  window.setTimeout(() => $('#toast').classList.remove('show'), 2800);
};

$('#conceptSearch').addEventListener('input', (event) => {
  const query = event.target.value.toLowerCase();
  $$('.concept').forEach((item) => {
    item.hidden = !item.textContent.toLowerCase().includes(query);
  });
});

$$('.taxonomy-tabs button').forEach((tab) => tab.addEventListener('click', () => {
  $$('.taxonomy-tabs button').forEach((item) => {
    item.classList.toggle('active', item === tab);
    item.setAttribute('aria-selected', item === tab);
  });
  toast(tab.textContent, tab.textContent === 'Dimensions' ? 'Dimension axes are ready to browse.' : 'Showing taxonomy concepts.');
}));

$$('.tree-row').forEach((row) => row.addEventListener('click', () => {
  row.classList.toggle('open');
  const arrow = $('.chevron', row);
  arrow.textContent = row.classList.contains('open') ? '⌄' : '›';
}));

let draggedConcept = null;
$$('.concept').forEach((concept) => {
  concept.addEventListener('dragstart', () => {
    draggedConcept = concept;
    concept.style.opacity = '.55';
  });
  concept.addEventListener('dragend', () => { concept.style.opacity = ''; });
});

$$('.drop-target').forEach((target) => {
  target.addEventListener('dragover', (event) => { event.preventDefault(); target.classList.add('drag-over'); });
  target.addEventListener('dragleave', () => target.classList.remove('drag-over'));
  target.addEventListener('drop', (event) => {
    event.preventDefault();
    target.classList.remove('drag-over', 'plain-value');
    target.classList.add('tagged-value');
    const label = draggedConcept?.querySelector('span').textContent || 'Selected concept';
    target.dataset.currentTag = draggedConcept?.dataset.tag.split(':').pop() || 'SelectedConcept';
    target.insertAdjacentHTML('beforeend', `<span>${label}</span>`);
    draggedConcept?.classList.add('tagged');
    if (draggedConcept) $('i', draggedConcept).textContent = '✓';
    selectValue(target, label);
    toast('Disclosure tagged', `${label} was applied successfully.`);
  });
});

function selectValue(element, explicitLabel) {
  const label = explicitLabel || element.querySelector('span')?.textContent || 'Tagged value';
  $('#selectedValue').textContent = `£${Number(element.dataset.value).toLocaleString('en-GB')}`;
  $('#selectedValue').nextElementSibling.textContent = label;
  $('#conceptLabel').textContent = label;
  $('#conceptId').textContent = `uk-gaap:${element.dataset.currentTag || label.replaceAll(' ', '')}`;
}

$$('.tagged-value, .suggested-value').forEach((item) => item.addEventListener('click', () => selectValue(item)));
$('#saveTag').addEventListener('click', () => toast('Tag saved', 'Your changes passed basic validation.'));
$('#removeTag').addEventListener('click', () => toast('Tag removed', 'The value is now untagged.'));
$('#addDimension').addEventListener('click', () => {
  $('#dimensionState').textContent = 'Consolidation basis · Company only';
  $('#dimensionState').style.borderStyle = 'solid';
  toast('Dimension added', 'Company-only member has been applied.');
});

const modal = $('#validationModal');
$('#validateBtn').addEventListener('click', () => modal.showModal());
$('#exportBtn').addEventListener('click', () => modal.showModal());
$('#closeModal').addEventListener('click', () => modal.close());
$('#continueBtn').addEventListener('click', () => modal.close());
modal.addEventListener('click', (event) => { if (event.target === modal) modal.close(); });

$$('.doc-tools button').forEach((button) => button.addEventListener('click', () => {
  if (button.textContent === '+' || button.textContent === '−') toast('View updated', `Document zoom ${button.textContent === '+' ? 'increased' : 'decreased'}.`);
}));
