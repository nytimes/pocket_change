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
	this.isEmpty = function() {
		return isEmpty(this.conditionMap);
	};
	this.appendTo = function(domElement, withSpacer, appendIfEmpty) {
		withSpacer = typeof withSpacer !== 'undefined' ? withSpacer : false;
		appendIfEmpty = typeof appendIfEmpty !== 'undefined' ? appendIfEmpty : true;
		if (appendIfEmpty || !this.isEmpty()) {
			if (!('domConditionList' in this)) {
				this.buildList();
			};
			domElement.appendChild(this.domConditionContainer);
			if (withSpacer) {
				appendSpacerDiv(domElement);
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
	jiraStatusConditionGroup.appendTo(domCaseFilters, true, false);
	executionStatusConditionGroup.appendTo(domCaseFilters, true, false);
};

function buildSourceConditionName(sourceTokens, rootI, sliceEnd) {
	
	if (rootI === 0) {
		var root = sourceTokens[rootI];
	} else {
		var root = '.' + sourceTokens[rootI];
	};
	if (rootI === sourceTokens.length - 1) {
		return root;
	} else {
		conditionName = root + '.';
		for (var i = rootI + 1; i < sliceEnd; i++) {
			conditionName += sourceTokens[i];
			if (i < sourceTokens.length - 1) {
				conditionName += '.';
			};
		};
	};
	return conditionName;
};

function initDetailsFilters() {
	var messageSourceConditionGroup = new ConditionGroup('message_source_filter',
														 'Show sources:');
	var messageLevelConditionGroup = new ConditionGroup('message_level_filter',
														"Show levels:");
	var domLog = document.querySelector('li.log');
	var logIndex = 0;
	while (domLog !== null) {
		var node = new FilterableNode(domLog, new Filter(logIndex, 'any'));
		var sourceFilter = new Filter('logSource', 'any');
		node.addCondition(sourceFilter);
		var source = domLog.querySelector('div.source').textContent.trim();
		var sourceTokens = source.split(".");
		console.log(sourceTokens);
		for (var rootI = 0; rootI < sourceTokens.length; rootI++) {
			for (var endI = rootI + 1; endI <= sourceTokens.length; endI++) {
				var conditionName = buildSourceConditionName(sourceTokens, rootI, endI);
				console.log(conditionName);
				var condition = messageSourceConditionGroup.getCondition(conditionName);
				sourceFilter.addCondition(condition);
			};
		};
		var level = domLog.querySelector('div.level').textContent.trim();
		var condition = messageLevelConditionGroup.getCondition(level);
		node.addCondition(condition);
		domLog = nextSiblingNode(domLog);
		logIndex++;
	};
	var domLogFilters = document.querySelector('div.log_filters');
	appendSpacerDiv(domLogFilters);
	messageSourceConditionGroup.appendTo(domLogFilters, true, false);
	messageLevelConditionGroup.appendTo(domLogFilters, true, false);
};