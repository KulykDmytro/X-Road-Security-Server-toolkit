from cement import App, TestApp
from cement.core.exc import CaughtSignal

from .core.exc import XRDSSTError
from .controllers.init import Init
from .controllers.token import TokenController



class XRDSST(App):
    """X-Road Security Server Toolkit primary application."""

    class Meta:
        label = 'xrdsst'

        # call sys.exit() on close
        exit_on_close = True

        # load additional framework extensions
        extensions = ['yaml']

        # register handlers
        handlers = [Init]


class XRDSSTTest(TestApp, XRDSST):
    """A sub-class of XRDSST that is better suited for testing."""

    class Meta:
        label = 'xrdsst'


def main():
    with XRDSST() as app:
        try:
            app.run()

        except AssertionError as e:
            print('AssertionError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except XRDSSTError as e:
            print('XRDSSTError > %s' % e.args[0])
            app.exit_code = 1

            if app.debug is True:
                import traceback
                traceback.print_exc()

        except CaughtSignal as e:
            # Default Cement signals are SIGINT and SIGTERM, exit 0 (non-error)
            print('\n%s' % e)
            app.exit_code = 0


if __name__ == '__main__':
    main()
