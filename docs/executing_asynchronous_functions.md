# Using asynchronous functions (coroutines) in components

You can use coroutines (asnychronous functions defined with `async def`) in components. To do this just edit the main function declaration to start with `async def` instead of `def`.

After that you can await other coroutines defined in your component code or imported from libraries from within the async main function. During component execution hetida designer automatically detects whether your main definition is an ordinary synchronous function or a coroutine. In the later case it will await your main function in the runtime's main event loop.

Note that async main functions of workflow operators are not executed in parallel, but the component adapter runs all component adapter wiring executions in parallel. So this in particular is recommended for components that are meant to be used via the component adapter (and typically are io bound).


> :warning: Except for adding `async`, all changes in the automatically generated main function header will be reversed with the next autosave, which happens every few seconds.