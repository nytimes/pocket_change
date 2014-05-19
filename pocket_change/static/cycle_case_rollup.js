function isEmpty(obj) {
	for (var name in obj) {
		if (obj.hasOwnProperty(name)) {
			return false;
		};
	};
	return true;
};

function nextSiblingNode(node) {
	var next = node.nextSibling;
	while (next !== null && next.nodeType != 1) {
		next = next.nextSibling;
	};
	return next;
};

function allFilterActive(conditionMap) {
	for (var condition in conditionMap) {
		if (!conditionMap[condition].state) {
			return false;
		};
	};
	return true;
};

function anyFilterActive(conditionMap) {
	for (var condition in conditionMap) {
		if (conditionMap[condition].state) {
			return true;
		};
	};
	return false;
};

function Filter(name, filterActive) {
	this.name = name;
	if (typeof filterActive == 'undefined' || filterActive == 'all') {
		this.filterActive = allFilterActive;
	} else if (filterActive == 'any') {
		this.filterActive = anyFilterActive;
	} else {
		this.filterActive = filterActive;
	};
	this.state = false;
	this.conditionMap = {};
	this.filters = [];
	this.addFilter = function(filter) {
		this.filters.push(filter);
	};
	this.addCondition = function(condition) {
		this.conditionMap[condition.name] = condition;
		condition.addFilter(this);
	};
	this.update = function() {
		this.state = this.filterActive(this.conditionMap);
		for (var i = 0; i < this.filters.length; i++) {
			this.filters[i].update();
		};
	};
};

function FilterableNode(domElement, filter) {
	this.domElement = domElement;
	this.filter = filter;
	this.update = function() {
		this.domElement.setAttribute('filtered', this.filter.state ? 'y' : 'n');
	};
	filter.addFilter(this);
	this.addCondition = function(condition) {
		this.filter.addCondition(condition);
	};
};

function Condition(name, domElement) {
	this.name = name;
	domElement.setAttribute('active', 'n');
	this.domElement = domElement;
	this.state = false;
	this.filters = [];
	var self = this;
	this.toggle = function() {
		self.state = self.state ? false : true;
		self.domElement.setAttribute('active', self.state ? 'y' : 'n');
		for (var i = 0; i < self.filters.length; i++) {
			self.filters[i].update();
		};
	};
	domElement.addEventListener('click', this.toggle, false);
	this.addFilter = function(filter) {
		this.filters.push(filter);
	};
};

function ConditionGroup(name, label) {
	this.name = name;
	this.label = label;
	this.conditionMap = {};
	this.rowWidth = 4;
	this.initContainer = function() {
		if (!('domConditionContainer' in this)) {
			this.domConditionContainer = document.createElement('div');
			this.domConditionContainer.className = this.name;
			var domConditionGroupLabel = document.createElement('div');
			domConditionGroupLabel.className = 'label';
			domConditionGroupLabel.appendChild(document.createTextNode(this.label));
			this.domConditionContainer.appendChild(domConditionGroupLabel);
			this.domConditionList = document.createElement('ul');
			this.domConditionList.className = 'filter_list';
			this.domConditionContainer.appendChild(this.domConditionList);
		};
	};
	this.getCondition = function(conditionName) {
		if (conditionName in this.conditionMap) {
			return this.conditionMap[conditionName];
		} else {
			var condition = document.createElement('li');
			condition.appendChild(document.createTextNode(conditionName));
			condition = new Condition(conditionName, condition);
			this.conditionMap[conditionName] = condition;
			return condition;
		};
	};
	this.buildList = function() {
		this.initContainer();
		var names = [];
		for (var name in this.conditionMap) {
			if (this.conditionMap.hasOwnProperty(name)) {
				names.push(name);
			};
		};
		names.sort();
		for (var i = 0; i < names.length; i++) {
			this.domConditionList.appendChild(this.conditionMap[names[i]].domElement);
		};
		this.setRowWidth();
	};
	this.setRowWidth = function(rowWidth) {
		if (typeof rowWidth !== 'undefined') {
			this.rowWidth = rowWidth;
		} else {
			rowWidth = this.rowWidth;
		};
		if ('domConditionList' in this) {
			var index = 0;
			var domConditions = this.domConditionList.childNodes;
			for (var i = 0; i < domConditions.length; i++) {
				var domCondition = domConditions[i];
				domCondition.setAttribute('row', Math.floor(i / rowWidth));
				domCondition.setAttribute('column', i % rowWidth);
			};
		};
	};
};

function appendSpacerDiv(domElement) {
	var spacer = document.createElement('div');
	spacer.className = 'spacer';
	domElement.appendChild(spacer);
};

function initRollupFilters() {
	var executionStatusConditionGroup = new ConditionGroup('execution_result_filter',
														   'Show with:');
	var jiraStatusConditionGroup = new ConditionGroup('jira_status_filter',
													  'Show:');

	var domCase = document.querySelector('li.case');
	while (domCase !== null) {
		var caseId = domCase.querySelector('div.case_id').textContent.trim();
		var node = new FilterableNode(domCase, new Filter(caseId, 'any'));
		var executionStatusFilter = new Filter('executionStatus');
		node.addCondition(executionStatusFilter);
		var domExecution = domCase.querySelector('li.execution');
		while (domExecution !== null) {
			var status = domExecution.querySelector('div.result_status div').textContent.trim();
			var condition = executionStatusConditionGroup.getCondition(status);
			executionStatusFilter.addCondition(condition);
			domExecution = nextSiblingNode(domExecution);
		};
		var domJiraStatus = domCase.querySelector('div.jira_summary');
		if (domJiraStatus !== null) {
			var status = domJiraStatus.textContent.trim();
			var condition = jiraStatusConditionGroup.getCondition(status);
			node.addCondition(condition);
		};
		domCase = nextSiblingNode(domCase);
	};
	var domCaseFilters = document.querySelector('div.case_filters');
	appendSpacerDiv(domCaseFilters);
	if (!isEmpty(jiraStatusConditionGroup.conditionMap)) {
		jiraStatusConditionGroup.buildList();
		domCaseFilters.appendChild(jiraStatusConditionGroup.domConditionContainer);
		appendSpacerDiv(domCaseFilters);
	};
	if (!isEmpty(executionStatusConditionGroup.conditionMap)) {
		executionStatusConditionGroup.buildList();
		domCaseFilters.appendChild(executionStatusConditionGroup.domConditionContainer);
		appendSpacerDiv(domCaseFilters);
	};
};