from enum import IntFlag

import comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0 as __wrapper_module__
from comtypes.gen._00020430_0000_0000_C000_000000000046_0_2_0 import (
    OLE_YPOS_HIMETRIC, OLE_XSIZE_CONTAINER, IFont, Gray, COMMETHOD,
    IPicture, Default, Color, IFontDisp, IEnumVARIANT, StdPicture,
    OLE_HANDLE, VARIANT_BOOL, DISPMETHOD, OLE_YPOS_CONTAINER,
    _check_version, OLE_YSIZE_CONTAINER, StdFont, IDispatch,
    OLE_XSIZE_HIMETRIC, OLE_ENABLEDEFAULTBOOL, FONTSIZE, FONTBOLD,
    Library, HRESULT, DISPPARAMS, _lcid, OLE_YPOS_PIXELS, Picture,
    typelib_path, FONTUNDERSCORE, OLE_YSIZE_HIMETRIC, GUID,
    IPictureDisp, EXCEPINFO, OLE_XPOS_PIXELS, BSTR, FONTITALIC,
    Unchecked, Monochrome, OLE_XPOS_CONTAINER, OLE_CANCELBOOL,
    IFontEventsDisp, IUnknown, DISPPROPERTY, OLE_XPOS_HIMETRIC,
    OLE_XSIZE_PIXELS, FONTNAME, FontEvents, CoClass, OLE_OPTEXCLUSIVE,
    VgaColor, OLE_COLOR, FONTSTRIKETHROUGH, dispid, OLE_YSIZE_PIXELS,
    Font, Checked
)


class OLE_TRISTATE(IntFlag):
    Unchecked = 0
    Checked = 1
    Gray = 2


class LoadPictureConstants(IntFlag):
    Default = 0
    Monochrome = 1
    VgaColor = 2
    Color = 4


__all__ = [
    'OLE_YPOS_HIMETRIC', 'OLE_XSIZE_CONTAINER', 'OLE_YPOS_PIXELS',
    'IFont', 'Gray', 'OLE_TRISTATE', 'Picture', 'typelib_path',
    'IPicture', 'FONTUNDERSCORE', 'Default', 'OLE_YSIZE_HIMETRIC',
    'Color', 'IFontDisp', 'StdPicture', 'OLE_HANDLE', 'IPictureDisp',
    'OLE_XPOS_PIXELS', 'FONTITALIC', 'Unchecked', 'Monochrome',
    'OLE_XPOS_CONTAINER', 'OLE_CANCELBOOL', 'IFontEventsDisp',
    'OLE_YPOS_CONTAINER', 'OLE_XPOS_HIMETRIC', 'OLE_XSIZE_PIXELS',
    'FONTNAME', 'OLE_YSIZE_CONTAINER', 'StdFont', 'FontEvents',
    'LoadPictureConstants', 'OLE_XSIZE_HIMETRIC', 'OLE_OPTEXCLUSIVE',
    'VgaColor', 'OLE_COLOR', 'OLE_ENABLEDEFAULTBOOL', 'FONTSIZE',
    'FONTSTRIKETHROUGH', 'FONTBOLD', 'Library', 'OLE_YSIZE_PIXELS',
    'Font', 'Checked'
]

