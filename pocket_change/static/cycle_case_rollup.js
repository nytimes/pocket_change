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
function initFilterGroup(filterName, statusLocator, label, getCaseFromStatus) {
	var statusNodes = document.querySelectorAll(statusLocator);
	if (statusNodes.length > 0) {
		var statusFilterNodes = {};
		var statusKeys = [];
		// Lists of case nodes for which listeners are attached by status key
		var statusKeyCaseNodeMap = {};
		for (var i = 0; i < statusNodes.length; i++) {
			var key = statusNodes[i].textContent.trim();
			var caseNode = getCaseFromStatus(statusNodes[i]);
			var filterNode;
			if (key in statusFilterNodes) { filterNode = statusFilterNodes[key]; }
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
				statusKeys.push(key);
				statusFilterNodes[key] = filterNode; 
				filterNode.className = statusNodes[i].className + '_' + filterName;
			};
			var alreadyListening = false;
			if (key in statusKeyCaseNodeMap) {
				for (var j = 0; j < statusKeyCaseNodeMap[key].length; j++) {
					if (statusKeyCaseNodeMap[key][j] == caseNode) {
						alreadyListening = true;
					};
				};
			} else { statusKeyCaseNodeMap[key] = []; };
			if (!alreadyListening) {
				filterNode.addEventListener('click',
										filterListeners.getListener(caseNode,
																filterName),
										false);
				statusKeyCaseNodeMap[key].push(caseNode);
			};
		};
		statusKeys.sort();
		var statusFiltersContainer = document.createElement('div');
		statusFiltersContainer.className = filterName;
		var labelContainer = document.createElement('div');
		labelContainer.className = 'label';
		labelContainer.appendChild(document.createTextNode(label));
		statusFiltersContainer.appendChild(labelContainer);
		var statusFilters = document.createElement('ul');
		statusFilters.className = 'filter_list';
		statusFiltersContainer.appendChild(statusFilters);
		for (var i = 0; i < statusKeys.length; i++) {
			filterNode = statusFilterNodes[statusKeys[i]];
			filterNode.setAttribute('column', i % 4);
			filterNode.setAttribute('row', Math.floor(i / 4));
			statusFilters.appendChild(statusFilterNodes[statusKeys[i]]);
		};
		caseFiltersNode = document.querySelector('div.case_filters');
		if (caseFiltersNode.childNodes.length == 0) {
			spacer = document.createElement('div');
			spacer.className = 'spacer';
			caseFiltersNode.appendChild(spacer);
		}
		document.querySelector('div.case_filters').appendChild(statusFiltersContainer);
		spacer = document.createElement('div');
		spacer.className = 'spacer';
		caseFiltersNode.appendChild(spacer);
	};
};
function initFilters() {
	initFilterGroup('jira_status_filter',
					'li.case div.jira_summary div',
					'Show:',
					function(statusNode) {
						return statusNode.parentNode.parentNode.parentNode;
					});
	initFilterGroup('execution_result_filter',
					'li.execution div.result div',
					'Show with:',
					function(statusNode) {
						return statusNode.parentNode.parentNode.parentNode.parentNode;
					});
};