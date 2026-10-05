"""Misconception rule modules.

Importing this package does not auto-import the rules; the engine iterates the
package and imports each module so the ``@register`` decorators run. Keeping
the import explicit (engine-driven) avoids import-order surprises.
"""
