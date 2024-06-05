from guidance import models, select, gen, system, assistant, user

def prepare_model(lm: models.Model):
    with system():
        lm += "You are a book information generator. Generate a JSON structure representing a book with the following properties: title, author, and publication date. Generate the author property first."
    with user():
        lm += "The book is called 'The Great Gatsby', written by F. Scott Fitzgerald, and was published in 1925."
    return lm

def test_with_gen(selected_model: models.Model):
    lm = prepare_model(selected_model)
    with assistant():
        lm += gen(max_tokens=100)
    print(lm)
    assert lm == "Hello"

def test_with_select(selected_model: models.Model):
    lm = prepare_model(selected_model)
    with assistant():
        lm += select(["\"author\"", "\"title\""]) + gen(max_tokens=100)
    print(lm)
    assert lm == "Hello"
