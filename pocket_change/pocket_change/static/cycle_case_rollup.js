function FilterListener(caseNode) {
	this.caseNode = caseNode;
	this.listenerMap = {};
	this.listenerNames = [];
	this.getFire = function(trackName) {
		if (trackName in this.listenerMap) { return this.listenerMap[trackName]; }
		else {
			var self = this;
			this.listenerNames.push(trackName);
			var fire = function() {
				var filtered = 'n';
				var set = (self.caseNode.getAttribute(trackName) == 'y' ? 'n' : 'y');
				self.caseNode.setAttribute(trackName, set);
				for (var i = 0; i < self.listenerNames.length; i++) {
					if (self.caseNode.getAttribute(self.listenerNames[i]) == 'y') {
						filtered = 'y';
					};
				}; 
				self.caseNode.setAttribute('filtered', filtered);
			};
			this.listenerMap[trackName] = fire;
			return fire;
		};
	};
};
function FilterListenerStore() {
	this.caseNodeListeners = [];
	this.getListener = function(caseNode, trackName) {
		var listener = 0;
		for (var i = 0; i < this.caseNodeListeners.length; i++) {
			if (this.caseNodeListeners[i].caseNode == caseNode) {
				listener = this.caseNodeListeners[i];
			};
		};
		if (listener == 0) {
			listener = new FilterListener(caseNode);
			this.caseNodeListeners.push(listener);
		};
		return listener.getFire(trackName);
	};
};
var filterListeners = new FilterListenerStore();
function initFilters() {
	var jiraCaseStatusNodes = document.querySelectorAll('li.case div.jira_summary div');
	if (jiraCaseStatusNodes.length > 0) {
		var jiraStatusFilterNodes = {};
		var jiraStatusKeys = [];
		for (var i = 0; i < jiraCaseStatusNodes.length; i ++) {
			var key = jiraCaseStatusNodes[i].textContent.trim();
			var caseNode = jiraCaseStatusNodes[i].parentNode.parentNode.parentNode;
			var filterNode;
			if (key in jiraStatusFilterNodes) { filterNode = jiraStatusFilterNodes[key]; }
			else {
				filterNode = document.createElement('li');
				filterNode.setAttribute('active', 'y');
				filterNode.addEventListener('click',
							function() {
								set = (this.getAttribute('active') == 'n' ? 'y' : 'n');
								this.setAttribute('active', set);
							},
							false);
				filterNode.appendChild(document.createTextNode(key));
				jiraStatusKeys.push(key);
				jiraStatusFilterNodes[key] = filterNode; 
				filterNode.className = jiraCaseStatusNodes[i].className + '_jira_status_filter';
			};
			filterNode.addEventListener('click',
									filterListeners.getListener(caseNode,
															'jira_status_filter'),
									false);
		};
		jiraStatusKeys.sort();
		var jiraStatusFiltersContainer = document.createElement('div');
		jiraStatusFiltersContainer.className = 'jira_status_filters';
		jiraStatusFiltersContainer.appendChild(document.createTextNode('Show:'));
		var jiraStatusFilters = document.createElement('ul');
		jiraStatusFilters.className = 'filter_list';
		jiraStatusFiltersContainer.appendChild(jiraStatusFilters);
		for (var i = 0; i < jiraStatusKeys.length; i++) {
			jiraStatusFilters.appendChild(jiraStatusFilterNodes[jiraStatusKeys[i]]);
		};
		document.body.appendChild(jiraStatusFiltersContainer);
	};
	var executionResultNodes = document.querySelectorAll('li.execution div.result div');
	var executionResultFilterNodes = {};
	var executionResultKeys = [];
	// Lists of case nodes for which listeners are attached by execution result key
	var executionResultKeyCaseNodeMap = {};
	for (var i = 0; i < executionResultNodes.length; i ++) {
		var key = executionResultNodes[i].textContent.trim();
		var caseNode = executionResultNodes[i].parentNode.parentNode.parentNode.parentNode;
		var filterNode;
		if (key in executionResultFilterNodes) { filterNode = executionResultFilterNodes[key]; }
		else {
			filterNode = document.createElement('li');
			filterNode.setAttribute('active', 'y');
			filterNode.addEventListener('click',
						function() {
							set = (this.getAttribute('active') == 'n' ? 'y' : 'n');
							this.setAttribute('active', set);
						},
						false);
			filterNode.appendChild(document.createTextNode(key));
			executionResultKeys.push(key);
			executionResultFilterNodes[key] = filterNode; 
			filterNode.className = executionResultNodes[i].className + '_execution_filter';
		};
		var alreadyListening = false;
		if (key in executionResultKeyCaseNodeMap) {
			for (var j = 0; j < executionResultKeyCaseNodeMap[key].length; j++) {
				if (executionResultKeyCaseNodeMap[key][j] == caseNode) {
					alreadyListening = true;
				};
			};
		} else { executionResultKeyCaseNodeMap[key] = []; };
		if (!alreadyListening) {
			filterNode.addEventListener('click',
						filterListeners.getListener(caseNode,
									'execution_status_filter'),
						false);
			executionResultKeyCaseNodeMap[key].push(caseNode);
		};
			
	};
	executionResultKeys.sort();
	var executionFiltersContainer = document.createElement('div');
	executionFiltersContainer.className = 'execution_filters';
	executionFiltersContainer.appendChild(document.createTextNode('Show with:'));
	var executionFilters = document.createElement('ul');
	executionFilters.className = 'filter_list';
	executionFiltersContainer.appendChild(executionFilters);
	for (var i = 0; i < executionResultKeys.length; i++) {
		executionFilters.appendChild(executionResultFilterNodes[executionResultKeys[i]]);
	};
	document.body.appendChild(executionFiltersContainer);
};