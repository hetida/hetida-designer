# Using asynchronous functions (coroutines) in components

You can use coroutines (asnychronous functions defined with `async def`) in components. To do this just edit the main function declaration to start with `async def` instead of `def`.

After that you can await other coroutines defined in your component code or imported from libraries from within the async main function. During component execution hetida designer automatically detects whether your main definition is an ordinary synchronous function or a coroutine. In the later case it will await your main function in the runtime's main event loop.

> :warning: Except for adding `async`, all changes in the automatically generated main function header will be reversed with the next autosave, which happens every few seconds.