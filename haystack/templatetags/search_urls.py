from django import template, http

register = template.Library()

class HaystackURLNode(template.Node):
    def __init__(self, kwargs):
        self.kwargs = kwargs
        self.action = kwargs[0]
#        self.action = action
#        self.value = value
    
    def _get_data(self, context, **kwargs):
        form = context['form']
        data = form.data.copy()
        if 'page' in kwargs and 'page' in data:
            if not kwargs['page']:
                data.__delitem__('page')
        return data
    
    def _url(self, context, data):
        request = context['request']

        url = request.path
        if len(data) > 0: 
            p = []
            "imperfect copy of urllib.encode because the values we have "
            "should already be urlencoded"
            for k, v in data.items():
                if isinstance(v, str):                    
                    p.append(k + "=" + data[k])
                elif isinstance(v, unicode):
                    p.append(k + "=" + v)
                else:
                    for vi in v:
                        p.append(k + "=" + vi)
            url += '?' + '&'.join(p)
        return url
    
    def page(self, context):
        """
        Construct a url for a specific page number. The search and faceting 
        parameters are added to the link
        """
        data = self._get_data(context)
        
        value = template.Variable(self.kwargs[1]).resolve(context)
        data.__setitem__('page', str(value))
        "work around go make selected_facets a list, is there a python/django way to do this?"
        if 'selected_facets' in data:
            data['selected_facets'] = data.getlist('selected_facets', None)
        return self._url(context, data)
    
    def add_facet(self, context):
        """
        Construct a url for adding a facet criteria to the search. For this 
        url the page variable is omitted from the parameters
        """
        data = self._get_data(context, page=False)

        field = self.kwargs[1]
        value = template.Variable(self.kwargs[2]).resolve(context)
        
        if 'selected_facets' in data:
            "get list will return a copy, update it in data when we are done"
            facets = data.getlist('selected_facets', None)
            for item in facets:
                if item.find(field) >= 0:
                    facets.remove(item)
            facets.append(field + ":" + value)
            data['selected_facets'] = facets
        else:
            data['selected_facets'] = field + ":" + http.quote(str(value))
        return self._url(context, data)
        
    def remove_facet(self, context):
        """
        Construct a url for removing a facet criteria from the search. For this
        url the page variable is omitted from the parameters
        """
        data = self._get_data(context, page=False)
        value = template.Variable(self.kwargs[1]).resolve(context)
        if 'selected_facets' in data:
            "getlist will return a copy, update it when doen"
            facets = data.getlist('selected_facets', None)
            for item in facets:
                if item.find(value) >= 0:
                    facets.remove(item)
            if len(facets) > 0:
                data['selected_facets'] = facets
            else:
                data.__delitem__('selected_facets')
        
        return self._url(context, data)
    
    def render(self, context):
        if self.action == "add_facet":
            return self.add_facet(context)
        elif self.action == "remove_facet":
            return self.remove_facet(context)
        elif self.action == "page":
            return self.page(context)
        
        return "unknown"
    
@register.tag(name = "haystack_url")
def haystack_url_add_facet(parser, token):
    try:
        args = token.split_contents()[1:]
    except ValueError:
        msg = "%r tag requires two arguments" % token.split_contents[0];
        raise template.TemplateSyntaxError(msg)
    return HaystackURLNode(args)
