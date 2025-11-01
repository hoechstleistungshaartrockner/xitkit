"""
Unit tests for the Location class.
"""

import pytest
from pathlib import Path
from xitkit.location import Location


class TestLocationInit:
    """Test Location initialization."""
    
    def test_init_default_values(self):
        """Test Location with default values."""
        location = Location()
        assert location.file_path == Path("todo.xit")
        assert location.line_numbers is None
    
    def test_init_with_none_file_path(self):
        """Test Location with None file_path."""
        location = Location(file_path=None)
        assert location.file_path == Path("todo.xit")
    
    def test_init_with_string_file_path(self):
        """Test Location with string file_path."""
        location = Location(file_path="test.xit")
        assert location.file_path == Path("test.xit")
    
    def test_init_with_path_object(self):
        """Test Location with Path object."""
        path = Path("test.xit")
        location = Location(file_path=path)
        assert location.file_path == path
    
    def test_init_with_none_line_numbers(self):
        """Test Location with None line_numbers."""
        location = Location(line_numbers=None)
        assert location.line_numbers is None
    
    def test_init_with_int_line_numbers(self):
        """Test Location with integer line_numbers."""
        location = Location(line_numbers=5)
        assert location.line_numbers == range(5, 6)
    
    def test_init_with_range_line_numbers(self):
        """Test Location with range line_numbers."""
        line_range = range(3, 8)
        location = Location(line_numbers=line_range)
        assert location.line_numbers == line_range
    
    def test_init_with_consecutive_list_line_numbers(self):
        """Test Location with consecutive list of line_numbers."""
        location = Location(line_numbers=[3, 4, 5, 6])
        assert location.line_numbers == range(3, 7)
    
    def test_init_with_unordered_consecutive_list(self):
        """Test Location with unordered but consecutive list."""
        location = Location(line_numbers=[5, 3, 4, 6])
        assert location.line_numbers == range(3, 7)
    
    def test_init_with_single_element_list(self):
        """Test Location with single element list."""
        location = Location(line_numbers=[5])
        assert location.line_numbers == range(5, 6)


class TestLocationInitErrors:
    """Test Location initialization error cases."""
    
    def test_init_with_non_consecutive_list(self):
        """Test Location raises error with non-consecutive list."""
        with pytest.raises(ValueError, match="line_numbers list must contain consecutive integers"):
            Location(line_numbers=[1, 3, 5])
    
    def test_init_with_gap_in_list(self):
        """Test Location raises error with gap in list."""
        with pytest.raises(ValueError, match="line_numbers list must contain consecutive integers"):
            Location(line_numbers=[1, 2, 4, 5])
    
    def test_init_with_non_integer_list_elements(self):
        """Test Location raises error with non-integer list elements."""
        with pytest.raises(TypeError, match="All elements in line_numbers list must be integers"):
            Location(line_numbers=[1, 2, "3", 4])
    
    def test_init_with_float_list_elements(self):
        """Test Location raises error with float list elements."""
        with pytest.raises(TypeError, match="All elements in line_numbers list must be integers"):
            Location(line_numbers=[1, 2, 3.5, 4])
    
    def test_init_with_invalid_line_numbers_type(self):
        """Test Location raises error with invalid line_numbers type."""
        with pytest.raises(TypeError, match="new_line_numbers must be an int or a range"):
            Location(line_numbers="invalid")


class TestLocationRepr:
    """Test Location string representation."""
    
    def test_repr_default(self):
        """Test Location repr with default values."""
        location = Location()
        expected = "Location(file_path=todo.xit, line_numbers=None)"
        assert repr(location) == expected
    
    def test_repr_custom_values(self):
        """Test Location repr with custom values."""
        location = Location(file_path="test.xit", line_numbers=range(3, 6))
        expected = "Location(file_path=test.xit, line_numbers=[3, 4, 5])"
        assert repr(location) == expected
    
    def test_repr_single_line(self):
        """Test Location repr with single line."""
        location = Location(file_path="file.txt", line_numbers=10)
        expected = "Location(file_path=file.txt, line_numbers=[10])"
        assert repr(location) == expected


class TestLocationEquality:
    """Test Location equality and hashing."""
    
    def test_equality_same_values(self):
        """Test equality with same values."""
        location1 = Location(file_path="test.xit", line_numbers=range(1, 4))
        location2 = Location(file_path="test.xit", line_numbers=range(1, 4))
        assert location1 == location2
    
    def test_equality_different_file_path(self):
        """Test inequality with different file_path."""
        location1 = Location(file_path="test1.xit", line_numbers=range(1, 4))
        location2 = Location(file_path="test2.xit", line_numbers=range(1, 4))
        assert location1 != location2
    
    def test_equality_different_line_numbers(self):
        """Test inequality with different line_numbers."""
        location1 = Location(file_path="test.xit", line_numbers=range(1, 4))
        location2 = Location(file_path="test.xit", line_numbers=range(2, 5))
        assert location1 != location2
    
    def test_equality_different_types(self):
        """Test inequality with different types."""
        location = Location()
        assert location != "not a location"
        assert location != 42
        assert location != None
    
    def test_hash_same_values(self):
        """Test hash consistency with same values."""
        location1 = Location(file_path="test.xit", line_numbers=range(1, 4))
        location2 = Location(file_path="test.xit", line_numbers=range(1, 4))
        assert hash(location1) == hash(location2)
    
    def test_hash_different_values(self):
        """Test hash difference with different values."""
        location1 = Location(file_path="test1.xit", line_numbers=range(1, 4))
        location2 = Location(file_path="test2.xit", line_numbers=range(1, 4))
        assert hash(location1) != hash(location2)
    
    def test_hash_in_set(self):
        """Test that Location objects can be used in sets."""
        location1 = Location(file_path="test.xit", line_numbers=1)
        location2 = Location(file_path="test.xit", line_numbers=1)
        location3 = Location(file_path="test.xit", line_numbers=2)
        
        location_set = {location1, location2, location3}
        assert len(location_set) == 2  # location1 and location2 are the same


class TestLocationSetFilePath:
    """Test Location set_file_path method."""
    
    def test_set_file_path_string(self):
        """Test setting file_path with string."""
        location = Location()
        location.set_file_path("new_file.xit")
        assert location.file_path == Path("new_file.xit")
    
    def test_set_file_path_path_object(self):
        """Test setting file_path with Path object."""
        location = Location()
        new_path = Path("new_file.xit")
        location.set_file_path(new_path)
        assert location.file_path == new_path
    
    def test_set_file_path_absolute_path(self):
        """Test setting file_path with absolute path."""
        location = Location()
        location.set_file_path("/absolute/path/file.xit")
        assert location.file_path == Path("/absolute/path/file.xit")


class TestLocationSetLineNumbers:
    """Test Location set_line_numbers method."""
    
    def test_set_line_numbers_none(self):
        """Test setting line_numbers to None."""
        location = Location(line_numbers=5)
        location.set_line_numbers(None)
        assert location.line_numbers is None
    
    def test_set_line_numbers_int(self):
        """Test setting line_numbers to integer."""
        location = Location()
        location.set_line_numbers(10)
        assert location.line_numbers == range(10, 11)
    
    def test_set_line_numbers_range(self):
        """Test setting line_numbers to range."""
        location = Location()
        new_range = range(5, 10)
        location.set_line_numbers(new_range)
        assert location.line_numbers == new_range
    
    def test_set_line_numbers_consecutive_list(self):
        """Test setting line_numbers to consecutive list."""
        location = Location()
        location.set_line_numbers([7, 8, 9, 10])
        assert location.line_numbers == range(7, 11)
    
    def test_set_line_numbers_unordered_consecutive_list(self):
        """Test setting line_numbers to unordered consecutive list."""
        location = Location()
        location.set_line_numbers([9, 7, 8, 10])
        assert location.line_numbers == range(7, 11)
    
    def test_set_line_numbers_single_list(self):
        """Test setting line_numbers to single element list."""
        location = Location()
        location.set_line_numbers([42])
        assert location.line_numbers == range(42, 43)


class TestLocationSetLineNumbersErrors:
    """Test Location set_line_numbers error cases."""
    
    def test_set_line_numbers_non_consecutive_list(self):
        """Test error with non-consecutive list."""
        location = Location()
        with pytest.raises(ValueError, match="line_numbers list must contain consecutive integers"):
            location.set_line_numbers([1, 2, 4, 5])
    
    def test_set_line_numbers_non_integer_list(self):
        """Test error with non-integer list elements."""
        location = Location()
        with pytest.raises(TypeError, match="All elements in line_numbers list must be integers"):
            location.set_line_numbers([1, 2, "3"])
    
    def test_set_line_numbers_invalid_type(self):
        """Test error with invalid type."""
        location = Location()
        with pytest.raises(TypeError, match="new_line_numbers must be an int or a range"):
            location.set_line_numbers("invalid")
    
    def test_set_line_numbers_float(self):
        """Test error with float."""
        location = Location()
        with pytest.raises(TypeError, match="new_line_numbers must be an int or a range"):
            location.set_line_numbers(3.14)


class TestLocationEdgeCases:
    """Test Location edge cases."""
    
    def test_empty_list_line_numbers(self):
        """Test behavior with empty list."""
        location = Location()
        with pytest.raises(IndexError):
            location.set_line_numbers([])
    
    def test_negative_line_numbers(self):
        """Test with negative line numbers."""
        location = Location(line_numbers=[-1, 0, 1])
        assert location.line_numbers == range(-1, 2)
    
    def test_zero_line_number(self):
        """Test with zero line number."""
        location = Location(line_numbers=0)
        assert location.line_numbers == range(0, 1)
    
    def test_large_line_numbers(self):
        """Test with large line numbers."""
        location = Location(line_numbers=range(1000000, 1000003))
        assert location.line_numbers == range(1000000, 1000003)
    
    def test_file_path_with_spaces(self):
        """Test file path with spaces."""
        location = Location(file_path="file with spaces.xit")
        assert location.file_path == Path("file with spaces.xit")
    
    def test_file_path_with_special_characters(self):
        """Test file path with special characters."""
        location = Location(file_path="file@#$%.xit")
        assert location.file_path == Path("file@#$%.xit")


class TestLocationIntegration:
    """Test Location integration scenarios."""
    
    def test_modify_after_creation(self):
        """Test modifying Location after creation."""
        location = Location(file_path="original.xit", line_numbers=1)
        
        # Modify file path
        location.set_file_path("modified.xit")
        assert location.file_path == Path("modified.xit")
        
        # Modify line numbers
        location.set_line_numbers(range(5, 10))
        assert location.line_numbers == range(5, 10)
    
    def test_location_as_dict_key(self):
        """Test using Location as dictionary key."""
        location1 = Location(file_path="test.xit", line_numbers=1)
        location2 = Location(file_path="test.xit", line_numbers=1)
        location3 = Location(file_path="test.xit", line_numbers=2)
        
        data = {
            location1: "value1",
            location3: "value3"
        }
        
        # location2 should map to same value as location1
        assert data[location2] == "value1"
        assert data[location3] == "value3"
        assert len(data) == 2
    
    def test_location_comparison_chain(self):
        """Test multiple location comparisons."""
        location1 = Location(file_path="a.xit", line_numbers=1)
        location2 = Location(file_path="a.xit", line_numbers=1)
        location3 = Location(file_path="b.xit", line_numbers=1)
        
        assert location1 == location2
        assert location1 != location3
        assert location2 != location3
        
        # Transitivity
        assert not (location1 == location2 and location2 == location3 and location1 != location3)